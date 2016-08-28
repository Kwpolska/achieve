"""Context processors for Achieve."""

from achieve import queries, models


def badges(request):
    """Generate badges to show off some numbers."""
    if not request.user.is_authenticated():
        return {'badges': {}}
    b = {}

    b['inbox'] = request.user.achieveprofile.badge_inbox
    b['all_tasks'] = request.user.achieveprofile.badge_all_tasks
    b['due_soon'] = queries.due_soon(request).count()
    b['trash'] = request.user.achieveprofile.badge_trash
    b['projects'] = request.user.achieveprofile.badge_projects

    return {'badges': b}


def pinned(request):
    """Add pinned tasks to context."""
    if not request.user.is_authenticated():
        return {'pinned_items': []}
    pins = []

    for i in queries.pinned_tasks(request).order_by("title"):
        pins.append(i)

    for i in models.Project.objects.filter(pinned=True, user=request.user, open=True).order_by("title"):
        pins.append(i)

    for i in models.Tag.objects.filter(pinned=True, user=request.user).order_by("title"):
        pins.append(i)

    return {"pinned_items": pins}
