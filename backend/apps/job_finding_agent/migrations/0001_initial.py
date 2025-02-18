# Generated by Django 5.1.5 on 2025-02-18 14:38

import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('job_scraping', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserJobFitEvaluation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Unique identifier for the user job fit evaluation', primary_key=True, serialize=False)),
                ('llm_score', models.IntegerField(help_text='Fit score from the LLM evaluation', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('llm_evaluation', models.TextField(help_text='Evaluation from the LLM')),
                ('user_score', models.IntegerField(blank=True, help_text='Fit score from the use. 0 to 5 stars', null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)])),
                ('user_feedback', models.TextField(blank=True, help_text='Feedback from the user. Text area on the frontend', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('job', models.ForeignKey(help_text='Job that is being evaluated', on_delete=django.db.models.deletion.CASCADE, to='job_scraping.job')),
                ('user', models.ForeignKey(help_text='User who is being evaluated', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Job Fit Evaluation',
                'verbose_name_plural': 'User Job Fit Evaluations',
            },
        ),
    ]
