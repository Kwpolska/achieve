"""Achieve template extras."""

from django import template
from django.core.urlresolvers import reverse
from django.utils.html import format_html, mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def badge(context, b):
    """Produce a numeric badge for an object."""
    if context['badges'][b]:
        return format_html(' <span class="badge">{0}</span>', context['badges'][b])
    else:
        return ''


@register.simple_tag()
def badge_count(queryset):
    """Produce a badge with a queryset count."""
    number = queryset.count()
    if number != 0:
        return format_html(' <span class="badge">{0}</span>', number)
    else:
        return ''


@register.simple_tag(takes_context=True)
def navbar_link(context, link, title, icon='fa-chevron-right', mobile_only=False):
    """Produce a navbar link."""
    li_class = []
    if context['request'].path == link:
        li_class.append('active')
        active_text = mark_safe('<span class="sr-only"> (active)</span>')
    else:
        active_text = ''

    if mobile_only:
        li_class += ['hidden-sm', 'hidden-md', 'hidden-lg']

    if li_class:
        li_class_h = format_html(' class="{0}"', ' '.join(li_class))
    else:
        li_class_h = ''

    return format_html('<li{2}><a href="{0}"><i class="fa fa-fw {4}"></i> {1}{3}</a></li>', link, title, li_class_h, active_text, icon)


@register.simple_tag(takes_context=True)
def navbar_entry(context, path, title, icon='fa-chevron-right', mobile_only=False):
    """Produce a navbar entry."""
    return navbar_link(context, reverse(path), title, icon, mobile_only)


@register.simple_tag(takes_context=True)
def navbar_user_entry(context, path, icon='fa-chevron-right', mobile_only=False):
    """Produce a navbar user entry."""
    user = context['request'].user
    # Display the full name of this user, or username if not available.
    title = user.get_full_name()
    if not title:
        title = user.username
    return navbar_link(context, reverse(path), title, icon, mobile_only)


@register.simple_tag(takes_context=True)
def navbar_pin(context, item):
    """Display a navbar pin."""
    return navbar_link(context, item.get_absolute_url(), item.title, 'fa-thumb-tack')


@register.simple_tag(takes_context=True)
def navbar_badge(context, path, title, b, icon='fa-chevron-right', mobile_only=False):
    """Produce a navbar entry with a badge."""
    title += badge(context, b)
    return navbar_entry(context, path, title, icon, mobile_only)


@register.simple_tag()
def folder_link(folder):
    """Link to a folder."""
    if folder == 'inbox':
        icon = 'fa-inbox'
        url = reverse('achieve:inbox')
    elif folder == 'tasks':
        icon = 'fa-tasks'
        url = reverse('achieve:tasks')
    elif folder == 'trash':
        icon = 'fa-trash'
        url = reverse('achieve:trash')
    else:
        icon = 'fa-question'
        url = '#'

    return format_html('<a href="{0}"><i class="fa {1}"></i> {2}</a>', url, icon, folder.capitalize())


@register.inclusion_tag('achieve/inc_task_table.html', takes_context=True)
def task_table(context, table, empty_msg, sortable=True):
    """Render a table of tasks."""
    return {'table': table, 'empty_msg': empty_msg, 'sortable': sortable, 'request': context['request']}


@register.inclusion_tag('achieve/inc_project_table.html', takes_context=True)
def project_table(context, table, empty_msg, sortable=True):
    """Render a table of tasks."""
    return {'table': table, 'empty_msg': empty_msg, 'sortable': sortable, 'request': context['request']}


@register.inclusion_tag('achieve/inc_task_filters.html', takes_context=True)
def task_filters(context, table, filter_form, show_no_project=True):
    """Render the task filters well."""
    return {'table': table, 'form': filter_form, 'show_no_project': show_no_project, 'request': context['request']}


@register.inclusion_tag('achieve/inc_project_filters.html', takes_context=True)
def project_filters(context, table, filter_form):
    """Render the project filters well."""
    return {'table': table, 'form': filter_form, 'request': context['request']}


PAGEFMT_CURRENT = '<li class="active"><a href="#">{0} <span class="sr-only">(current)</span></a></li>'
PAGEFMT_OMITTED = mark_safe('<li class="disabled"><a href="#">… <span class="sr-only">(omitted)</span></a></li>')
PAGEFMT_DEFAULT = '<li><a href="?{0}">{1}</a></li>'
PAGEFMT_PREVNEXT = '<li><a href="?{0}" aria-label="{1}"><span aria-hidden="true">&{2}aquo;</span></a></li>'
PAGEFMT_PREVNEXT_OFF = '<li class="disabled"><a href="#" aria-label="{1} (disabled)"><span aria-hidden="true">&{2}aquo;</span></a></li>'


def pf_link(num, current_page, request):
    """Return the appropriate link for this page."""
    if num == current_page:
        return PAGEFMT_CURRENT.format(num)
    else:
        qdict = request.GET.copy()
        qdict['page'] = num
        url = qdict.urlencode()
        return PAGEFMT_DEFAULT.format(url, num)


def format_pagination(current_page, pagecount, table, request):
    """Format pagination."""
    if pagecount <= 10:
        pages_to_display = list(range(1, pagecount + 1))
    else:
        pages_to_display = {1, 2, current_page - 2, current_page - 1,
                            current_page,
                            current_page + 1, current_page + 2,
                            pagecount - 1, pagecount}
        pages_to_display = [i for i in sorted(pages_to_display) if i > 0 and i <= pagecount]

    # Previous link
    if table.has_previous():
        qdict = request.GET.copy()
        qdict['page'] = table.previous_page_number()
        yield PAGEFMT_PREVNEXT.format(qdict.urlencode(), "Previous", "l")
    else:
        yield PAGEFMT_PREVNEXT_OFF.format(None, "Previous", "l")

    # Numbers
    yield pf_link(1, current_page, request)
    for prev, current in zip(pages_to_display, pages_to_display[1:]):
        if (current - prev) > 2:
            yield PAGEFMT_OMITTED
        elif (current - prev) == 2:
            # Special case: if the difference is 2, let’s just show the number
            yield pf_link(current - 1, current_page, request)
        yield pf_link(current, current_page, request)

    # Next link
    if table.has_next():
        qdict = request.GET.copy()
        qdict['page'] = table.next_page_number()
        yield PAGEFMT_PREVNEXT.format(qdict.urlencode(), "Next", "r")
    else:
        yield PAGEFMT_PREVNEXT_OFF.format(None, "Next", "r")


@register.simple_tag(takes_context=True)
def pagination(context, table):
    """Render a pagination widget."""
    if table.paginator.num_pages == 1:
        # Don’t render a widget if one is unnecessary.
        return ''
    pages = ''.join(format_pagination(table.number, table.paginator.num_pages, table, context['request']))
    return mark_safe('<nav class="pagination-container"><ul class="pagination">' + pages + '</ul></nav>')


@register.simple_tag(takes_context=True)
def sortable_head(context, getname, title):
    """Render a sortable table header."""
    # Check current status and figure out new order
    current = context['request'].GET.get(getname)
    if current == 'asc':
        new_order = 'desc'
        icon = 'fa-sort-asc'
        sorttext = 'descending'
    elif current == 'desc':
        new_order = 'asc'
        icon = 'fa-sort-desc'
        sorttext = 'ascending'
    else:
        new_order = 'asc'
        icon = 'fa-sort'
        sorttext = 'ascending'

    # Create new URL
    qdict = context['request'].GET.copy()
    qdict[getname] = new_order
    url = qdict.urlencode()

    return format_html('<a class="sortbtn" href="?{0}" title="Sort {1}"><i class="fa {2}"></i> {3}</a>',
                       url, sorttext, icon, title)
