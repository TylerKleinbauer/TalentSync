from django.db import models
from .fields import NullableIntegerField

class Job(models.Model):
    # Use a CharField as primary key since your IDs are strings
    id = models.CharField(max_length=255, primary_key=True, unique=True)
    externalUrl = models.URLField(blank=True, null=True)
    logo = models.URLField(blank=True, null=True)
    company_id = NullableIntegerField(blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    contact_firstName = models.CharField(max_length=255, blank=True, null=True)
    contact_lastName = models.CharField(max_length=255, blank=True, null=True)
    headhunterApplicationAllowed = models.BooleanField(default=False)
    initialPublicationDate = models.CharField(max_length=255, blank=True, null=True)
    isActive = models.BooleanField(default=False)
    isPaid = models.BooleanField(default=False)
    language_skills = models.TextField(blank=True, null=True)
    postalCode = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    cantonCode = models.CharField(max_length=50, blank=True, null=True)
    countryCode = models.CharField(max_length=50, blank=True, null=True)
    publicationDate = models.CharField(max_length=255, blank=True, null=True)
    publicationEndDate = models.CharField(max_length=255, blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    synonym = models.TextField(blank=True, null=True)
    template_lead = models.TextField(blank=True, null=True)
    template_title = models.TextField(blank=True, null=True)
    industry = NullableIntegerField(blank=True, null=True)
    regionID = NullableIntegerField(blank=True, null=True)
    employmentGrades = models.TextField(blank=True, null=True)
    employmentPositionIds = NullableIntegerField(blank=True, null=True)
    employmentTypeIds = NullableIntegerField(blank=True, null=True)

    def __str__(self):
        return self.template_title or self.id
    
    class Meta:
        db_table = 'jobs'
