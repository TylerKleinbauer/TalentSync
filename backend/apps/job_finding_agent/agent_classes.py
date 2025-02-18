from typing import List, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import operator


# Data Formats

class UserProfile(BaseModel):
    """
    A class used to represent a user profile
    """
    name: str = Field(description="User's name"    )
    work_experience: str = Field(description="User's work experience")
    skills: str = Field(description="User's skills")
    education: str = Field(description="User's education")
    certifications: str = Field(description="User's certifications")
    other_info: str = Field(description="Other relevant information")

class JobEvaluation(BaseModel):
    """
    A class used to represent the evaluations of the fit between the user and a job
    """
    job_id: str = Field(
        description="ID of the job being evaluated"
    )
    fit_scores: int = Field(
        description="List of fit scores between the user and a job"
    )
    fit_evaluations: str = Field(
        description="List of evaluations of the fit between the user and a job"
    )

class KeywordList(BaseModel):
    """
    A class used to represent a list of keywords
    """
    keywords: List[str] = Field(
        description="List of keywords"
    )

# States

class MultiJobEvaluationState(TypedDict):
    """
    State used in the overall graph that evaluates the fit between an individual and a list of jobs
    """
    user_id: str # The id of the user
    user_profile: UserProfile
    similarity_search_profile: List[str] # Contains the optimitzed profile for similarity search
    job_ids: List[str] # Will contain the id of each job from similarity search
    job_info: List[List[str]] # Will contain the 'id', 'company_name', 'template_title', 'template_lead','industry', 'regionID', 'employementGrades', 'employmentPositionIds', 'employmentTypeIds' for each job
    job_evaluations: Annotated[List[JobEvaluation], operator.add]
    user_score: int
    user_feedback: str # Feedback from the user after seeing proposed jobs. Can be used for reranking.

class SingleJobEvaluationState(TypedDict):
    """
    State used in the sends to get single job evaluations simultaneously
    """
    job: List[str] # Will contain the id, company name, job title, and job description
    user_profile: UserProfile
