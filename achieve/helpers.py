"""Achieve helpers."""

from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.middleware import csrf
from django.utils.html import format_html
from django.utils.text import slugify
from achieve.models import Task
from achieve import queries


def get_next(request, best_guess=None):
    """Get the next URL to go to."""
    if 'next' in request.POST:
        return request.POST['next']
    else:
        return best_guess or reverse('achieve:index')


def next_page(request, best_guess=None):
    """Go to the next page."""
    return HttpResponseRedirect(get_next(request, best_guess))


def undo_btn(text, path, request, action, *args, **kwargs):
    """Create an undo button."""
    return format_html("""<form action="{0}" method="POST">{3}
<input type="hidden" name="next" value="{1}">
<input type="hidden" name="csrfmiddlewaretoken" value="{4}">
<button class="btn-link alert-link" type="submit" name="action" value="{2}"><i class="fa fa-undo"></i> Undo</button>
</form>""", reverse(path, args=args, kwargs=kwargs), get_next(request), action, text, csrf.get_token(request))


def add_to_inbox(request, title, save=True):
    """Add a task to Inbox and return it."""
    t = Task()
    t.title = title
    t.folder = 'inbox'
    t.user = request.user
    if save:
        t.save()
    return t


def update_slug(obj, force=False, save=True):
    """Update the slug for an item."""
    # The slugbase is used to identify things with the same slug base.
    slugbase = slugify(obj.title)
    if slugbase == obj.slugbase and not force:
        # Assuming DB consistency, the slug is fine
        return

    samebase = obj.__class__.objects.filter(user=obj.user, slugbase=slugbase)
    if not samebase:
        # New slug base.
        final_slug = slugbase
    elif len(samebase) == 1 and samebase[0] == obj:
        # (If forced) only slug like this.
        final_slug = slugbase
    else:
        # We need to find a new slug for ourselves.
        others = samebase.exclude(slug=slugbase)
        if others:
            nums = [int(i.slug.split('-')[-1]) for i in others.all()]
            final_num = max(nums) + 1
        else:
            final_num = 1
        final_slug = "{0}-{1}".format(slugbase, final_num)

    obj.slugbase = slugbase
    obj.slug = final_slug
    if save:
        obj.save()


def update_badges(user):
    """Update all badges for a user/AchieveProfile."""
    p = user.achieveprofile
    p.badge_inbox = queries.inbox_user_notdone(user).count()
    p.badge_all_tasks = queries.incomplete_tasks_user(user).count()
    p.badge_trash = queries.trash_user(user).count()
    p.badge_projects = queries.open_projects_user(user).count()
    p.save()


def process_sorting(request, table, sortable, default_sort):
    """Process sorting."""
    use_default = True
    order = []
    for dbkey, getkey in sortable:
        if getkey in request.GET:
            use_default = False
            if request.GET[getkey] == 'asc':
                order.append(dbkey)
            else:
                order.append('-' + dbkey)
    if use_default:
        order = default_sort
    table = table.order_by(*order)
    return table


def process_pagination(request, table, identifier=''):
    """Process pagination."""
    paginator = Paginator(table, settings.ACHIEVE_ITEMS_PER_PAGE)
    page = request.GET.get('page' + identifier)
    try:
        table = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        table = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        table = paginator.page(paginator.num_pages)

    return table
