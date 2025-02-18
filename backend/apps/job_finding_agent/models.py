from django.db import models
from backend.apps.users.models import User
from backend.apps.job_scraping.models import Job
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

# Create your models here.

class UserJobFitEvaluation(models.Model):
    """
    Model to store user job fit evaluations
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the user job fit evaluation"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        help_text="User who is being evaluated"
    )
    
    job = models.ForeignKey(
        Job, 
        on_delete=models.CASCADE,
        help_text="Job that is being evaluated"
    )
    
    llm_score = models.IntegerField(
        help_text="Fit score from the LLM evaluation",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    llm_evaluation = models.TextField(
        help_text="Evaluation from the LLM"
    )
    
    user_score = models.IntegerField(
        help_text="Fit score from the use. 0 to 5 stars",
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        blank=True,
        null=True
    )

    user_feedback = models.TextField(
        help_text="Feedback from the user. Text area on the frontend",
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Job Fit Evaluation"
        verbose_name_plural = "User Job Fit Evaluations"

    def __str__(self):
        return f"{self.user.username} - {self.job.title}"

#class JobSearchHistory(models.Model):
    """
    Model to store job search history
    """
