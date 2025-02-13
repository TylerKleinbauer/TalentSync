from django.contrib import admin
from .models import DBUserProfile

@admin.register(DBUserProfile)
class DBUserProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'user__username', 'work_experience', 'skills')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'name')
        }),
        ('Professional Details', {
            'fields': ('work_experience', 'skills', 'education', 'certifications')
        }),
        ('Additional Information', {
            'fields': ('other_info',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
