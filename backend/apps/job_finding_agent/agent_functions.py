from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langgraph.types import Send
from django.contrib.auth import get_user_model

from backend.apps.job_scraping.models import Job
from backend.apps.job_finding_agent.agent_classes import SingleJobEvaluationState
from backend.settings import JOB_ADS_EMBEDDINGS_PATH
from backend.apps.job_finding_agent.agent_classes import UserProfile, JobEvaluation
from backend.apps.users.models import User
from backend.apps.profile_agent.models import DBUserProfile
from backend.apps.job_finding_agent.agent_classes import MultiJobEvaluationState, KeywordList
from config.llm_config import LLMFactory

User = get_user_model()

def retrieve_profile_from_db(state: MultiJobEvaluationState):
    """
    Retrieves the user profile from the database using user ID
    """
    user_id = state.get('user_id')
    print(f"Attempting to retrieve profile for user ID: {user_id}")

    try:
        # First get the user
        user = User.objects.get(id=user_id)
        print(f"Found user: {user.email}")
        %
        # Then get their profile through the OneToOne relationship
        profile = user.profile  # This works because of the related_name='profile' in DBUserProfile model
        print(f"Found profile for user: {profile.name}")
        
        # Convert to Pydantic model
        user_profile = UserProfile(
            name=profile.name,
            work_experience=profile.work_experience,
            skills=profile.skills,
            education=profile.education,
            certifications=profile.certifications,
            other_info=profile.other_info
        )
        return {'user_profile': user_profile}
    
    except User.DoesNotExist:
        print(f"No user found with ID: {user_id}")
        raise
    except Exception as e:
        print(f"Error retrieving profile: {str(e)}")
        raise

def prepare_profile_for_similarity_search(state: MultiJobEvaluationState):
    """ 
    Takes the raw userprofile and formats it for job retrieval
    """
    complete_profile = state['user_profile']
    print(f"Preparing profile for similarity search: {complete_profile.name}")
    
    llm_factory = LLMFactory()
    llm = llm_factory.get_llm(model_key='gpt-4o')

    profile_formatting_instructions = """"You are a recruitment expert specialized in matching candidate profiles to job openings. 
    Your task is to extract a concise list of keywords from the following candidate profile. 
    These keywords should capture the candidate's key skills, technical expertise, work experience, educational background, and any industry-specific terms that are relevant for job matching.

    Please follow these guidelines:
    1. Only extract keywords and key phrases explicitly mentioned in the profile.
    2. Do not invent or add any keywords that are not present.
    3. Focus on terms that are directly relevant to the candidate's qualifications and potential job fit.
    4. Return your answer in JSON format as a list of strings. For example:
    ["Python", "machine learning", "project management"]

    Candidate Profile:
    {complete_profile}

    Now, extract the keywords:
    """

    profile_formatting_instructions=profile_formatting_instructions.format(complete_profile=complete_profile)

    structured_llm = llm.with_structured_output(KeywordList)
    keyword_list = structured_llm.invoke([
        SystemMessage(content=profile_formatting_instructions),
        HumanMessage(content='Please create the list of keywords')
    ])
    print(f"Generated keywords: {keyword_list.keywords}")
    
    return {'similarity_search_profile': keyword_list}

def retrieve_id_similarity_search(state: MultiJobEvaluationState) -> MultiJobEvaluationState:
    """
    Retrieves job IDs based on similarity search of the profile keywords
    """
    # Get the state
    chroma_path = JOB_ADS_EMBEDDINGS_PATH
    similarity_search_profile = state.get('similarity_search_profile')  # Changed to match the key from previous function
    
    if not similarity_search_profile:
        print("No keywords found in state for similarity search")
        return {'job_ids': []}
    
    print(f"Running similarity search with keywords: {similarity_search_profile}")
    results_to_retrieve = 20

    # Initialize the embeddings
    embeddings = OpenAIEmbeddings(model='text-embedding-3-small')
    
    # Initialize the Chroma vector store
    vector_store = Chroma(
        collection_name="job_ads_embeddings",
        embedding_function=embeddings,
        persist_directory=chroma_path
    )
    
    # Convert KeywordList to string for similarity search
    search_text = ", ".join(similarity_search_profile.keywords)  # Access the keywords from the KeywordList model
    
    results = vector_store.similarity_search_with_relevance_scores(
        search_text,
        k=results_to_retrieve,
    )
    
    id_list = []
    for res in results:
        id_list.append(res[0].id)
        print(f"Found matching job: {res[0].metadata.get('job_title', 'Unknown Title')} (Score: {res[1]})")
    
    return {'job_ids': [id_list]}

def retrieve_jobs_from_ids(state: MultiJobEvaluationState):
    """
    Asynchronously retrieves Job records based on job IDs stored in the state using Django ORM.
    
    Args:
        state (ProfileState): The state containing job_ids.
    
    Returns:
        dict: A dictionary with the key 'all_jobs' mapping to a list of tuples
              (id, company_name, template_title, template_lead) for each Job.
    """
    # Retrieve the job_ids from the state.
    ids = state.get('job_ids', [])
    # Flatten the list of lists and remove duplicates.
    ids = list(set(item for sublist in ids for item in sublist))
    

    jobs_qs = list(
        Job.objects.filter(id__in=ids).values_list(
            'id', 
            'company_name', 
            'template_title', 
            'template_lead',
            'industry',
            'regionID',
            'employmentGrades',
            'employmentPositionIds',
            'employmentTypeIds'
        )
    )
    
    return {'job_info': jobs_qs}

def send_to_evaluate_fit(state: MultiJobEvaluationState) -> SingleJobEvaluationState:
    """
    Prepare the data to send to evaluate_fit for each job

    Args:
    state (MultiJobEvaluationState): state containing jobs and user profile

    Returns:
    list[Send]: list of Send objects, one for each job to evaluate
    """
    # Get the state
    jobs = state.get('job_info', [])
    user_profile = state.get('user_profile')
    
    print(f"Preparing to evaluate {len(jobs)} jobs")

    # Prepare a Send for each job
    sends = []
    for job in jobs:
        evaluate_fit_state = SingleJobEvaluationState({
            'user_profile': user_profile,
            'job': job
        })
        sends.append(Send('evaluate_fit', evaluate_fit_state))
    
    return sends

def evaluate_fit(state: SingleJobEvaluationState) -> MultiJobEvaluationState:
    """ 
    Evaluates the fit between the candidate and single job
    """
    # Initiate the llm
    llm_factory = LLMFactory()
    llm = llm_factory.get_llm(model_key='gpt-4o-mini')
    structured_llm = llm.with_structured_output(JobEvaluation)
    
    # Get the state
    job_id= state['job'][0]
    company_name= state['job'][1]
    job_title= state['job'][2]
    job_description= state['job'][3]
    user_profile= state['user_profile']
    
    # Write the system message
    system_message = """Your are a recruitement expert working for {company_name}.
    Your task is to evaluate the fit between a job you posted online and a user profile.
    
    The user profile is: {user_profile}
    
    The retrieved job information is:
    Job ID: 
    {job_id}
    Company Name: 
    {company_name}
    Job Title: 
    {job_title}
    Job Description: 
    {job_description}
    
    Please evaluate the fit between the user profile and the job along these lines:
    1) Does the candidate's core expertise align with the key requirements of the role?
    -Does the candidate possess the required hard skills (e.g., programming languages, financial modeling, data analysis)?
    -Do they have the necessary education, certifications, or training relevant to the role?
    -How well do their past work experiences align with the technical requirements of the position?
    
    2) How has the candidate's career trajectory prepared them for this role?
    - Has the candidate successfully performed similar tasks or projects in previous roles?
    - Can they demonstrate quantifiable achievements (e.g., increased revenue, improved efficiency)?
    - Do they have experience with the industry-specific tools, platforms, or methodologies?

    3. Does the candidate demonstrate problem-solving ability and initiative in their past roles?
    4. What motivates this candidate, and does it align with what this role offers?
    5. How does the candidate prefer to work, and does that match the company's culture?
    6. How well does the candidate communicate complex ideas, based on their profile?
    7. Does the candidate show a growth mindset and a willingness to learn?
    8. Are there any practical constraints (salary, location, logistics) that could impact fit?
    9. Are there any red flags or inconsistencies in their career history that require clarification?
    10. Does the candidate have the potential to grow within the organization beyond this role?
    
    Please evaluate the fit between the user profile and the job and provide a score between 1 and 100.
    Additionally, please write a brief rational explaining your evaluation of the fit between the user profile and the job.
    
    """
    # Format the system message
    system_message = system_message.format(
        company_name=company_name,
        job_id=job_id,
        job_title=job_title,
        job_description=job_description,
        user_profile=user_profile
    )
    
    # Generate the output
    job_evaluation = structured_llm.invoke([
        SystemMessage(content=system_message),
        HumanMessage(content="Can you evaluate the fit between the candidate and the job please?")
    ])
    
    # Add the job_id to the evaluation
    job_evaluation.job_id = job_id
    
    return {"job_evaluations": [job_evaluation]}