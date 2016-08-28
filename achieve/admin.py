"""Admin site (for AchieveProfiles only)."""

from django.contrib import admin
from achieve.models import AchieveProfile


class TaskAdmin(admin.ModelAdmin):
    """Customization for task administration view."""

    list_display = ('title', 'done', 'priority', 'folder')

admin.site.register(AchieveProfile)
