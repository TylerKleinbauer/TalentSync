from django.db import models

class DBUserProfile(models.Model):
    """
    Django model to store user profiles generated by the profile builder graph
    """
    name = models.CharField(
        max_length=255,
        help_text="User's name"
    )
    
    work_experience = models.TextField(
        help_text="User's work experience"
    )
    
    skills = models.TextField(
        help_text="User's skills"
    )
    
    education = models.TextField(
        help_text="User's education"
    )
    
    certifications = models.TextField(
        help_text="User's certifications",
        blank=True  # Allow this field to be empty
    )
    
    other_info = models.TextField(
        help_text="Other relevant information",
        blank=True  # Allow this field to be empty
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the profile was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the profile was last updated"
    )

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"Profile for {self.name}"
