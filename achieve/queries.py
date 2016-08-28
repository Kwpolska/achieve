"""Commonly used queries."""

from achieve.models import Task, Project, Tag
from django.utils import timezone
from datetime import timedelta


def inbox(request):
    """Get all tasks in the inbox that belong to the current user."""
    return Task.objects.select_related('project').filter(user=request.user, folder='inbox')


def inbox_user_notdone(user):
    """Get all tasks in the inbox that are not done and that belong to the specified user."""
    return Task.objects.select_related('project').filter(user=user, folder='inbox', done=False)


def all_tasks(request):
    """Get all tasks that belong to the current user."""
    return Task.objects.select_related('project').filter(user=request.user).exclude(folder='trash')


def incomplete_tasks_user(user):
    """Get all tasks that are not done and that belong to the specified user."""
    return Task.objects.filter(user=user, done=False).exclude(folder='trash')


def projects_with_tag(request, tag):
    """Get all projects with a tag that belong to the current user."""
    return tag.project_set.filter(user=request.user)


def tasks_with_tag(request, tag):
    """Get all tasks with a tag that belong to the current user."""
    return tag.task_set.filter(user=request.user).exclude(folder='trash')


def tasks_in_project(request, project):
    """Get all tasks in a project that belong to the current user."""
    return project.task_set.filter(user=request.user).exclude(folder='trash')


def trash(request):
    """Get all tasks in the trash that belong to the current user."""
    return Task.objects.select_related('project').filter(user=request.user, folder='trash')


def trash_user(user):
    """Get all tasks in the trash that belong to the specified user."""
    return Task.objects.select_related('project').filter(user=user, folder='trash')


def tags(request):
    """Get all tags that belong to the current user."""
    return Tag.objects.filter(user=request.user)


def open_projects(request):
    """Get all open projects that belong to the current user."""
    return Project.objects.prefetch_related('task_set').filter(user=request.user, open=True)


def open_projects_user(user):
    """Get all open projects that belong to the specified user."""
    return Project.objects.prefetch_related('task_set').filter(user=user, open=True)


def projects(request):
    """Get all projects that belong to the current user."""
    return Project.objects.prefetch_related('task_set').filter(user=request.user)


def due_soon(request):
    """Get all tasks that are due within one day or that are overdue."""
    soon = timezone.now() + timedelta(days=1)
    return Task.objects.select_related('project').filter(user=request.user, due__lt=soon, done=False).exclude(folder='trash')


def reminders_soon(request):
    """Get all tasks that have reminders due within 2 days."""
    now = timezone.now()
    soon = now + timedelta(days=2)
    return Task.objects.filter(
        user=request.user, reminder__lt=soon, reminder_seen=False, done=False).exclude(folder='trash')


def pinned_tasks(request):
    """Get all pinned tasks of the current user that are not in the Trash."""
    return Task.objects.filter(pinned=True, user=request.user).exclude(folder='trash')


def pinned_tasks_srp(request):
    """Get all pinned tasks of the current user that are not in the Trash (with Project data)."""
    return Task.objects.select_related('project').filter(pinned=True, user=request.user).exclude(folder='trash')
