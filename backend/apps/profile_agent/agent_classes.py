from typing import List
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

# Classes for the data

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

# Classes for the state

class ProfileState(TypedDict):
    user_docs: List[str]
    user_profile: UserProfile
    user_feedback: str