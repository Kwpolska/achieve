"""Achieve views."""

import collections
import pytz

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.views.generic import View

from achieve import queries
from achieve.forms import AddEditTaskForm, AddEditProjectForm, AddEditTagForm, TaskFilterForm, ProjectFilterForm, AchieveProfileForm
from achieve.helpers import next_page, undo_btn, add_to_inbox, process_pagination, update_badges
from achieve.models import Task, Tag, Project

# Generic views


class AchieveListView(View):
    title = None
    query = None
    badge_name = None
    empty_msg = "No results."
    filtered_msg = "No results."
    template = "achieve/tabular.html"
    sortable = ()
    default_sort = ()
    sort_prefix = ''

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        filter_form = self.filter_form(request.GET)
        if filter_form.is_valid():
            table = self.process_filters(request, args, kwargs, filter_form)
        table = self.process_sorting(request, table)
        table = process_pagination(request, table)
        if len(filter_form.data) > 1:  # filters were used, no pagination
            empty_msg = self.filtered_msg
        else:
            empty_msg = self.empty_msg
        context = {
            'title': self.title,
            'table': table,
            'empty_msg': empty_msg,
            'filter_form': filter_form,
        }
        if self.badge_name:
            context['badge_name'] = self.badge_name
        self.process_context(request, context)
        return render(request, self.template, context)

    def process_filters(self, request, args, kwargs, filter_form):
        """Process filters."""
        return self.query(request, *args, **kwargs)

    def process_sorting(self, request, table):
        """Process sorting."""
        use_default = True
        order = []
        for dbkey, getkey in self.sortable:
            if getkey in request.GET:
                use_default = False
                if request.GET[getkey] == 'asc':
                    order.append(dbkey)
                else:
                    order.append('-' + dbkey)
        if use_default:
            order = self.default_sort
        table = table.order_by(*order)
        return table

    def process_context(self, request, context):
        """Process context."""
        pass


class TaskListView(AchieveListView):
    filter_form = TaskFilterForm
    default_sort = ('done', '-due', '-added')
    sortable = (
        ('done', 's_done'),
        ('due', 's_due'),
        ('added', 's_added'),
        ('priority', 's_priority'),
        ('project', 's_project'),
        ('title', 's_title'),
    )
    new_location = ''
    show_add_button = True

    def process_filters(self, request, args, kwargs, filter_form):
        """Process filters and sorting."""
        q = self.query(request, *args, **kwargs)
        # TODO more filters?

        # Filter: done (nullable bool)
        done = filter_form.cleaned_data['done']
        if done != '-1':
            q = q.filter(done=(done == '1'))

        # Filter: priority (int)
        priority = filter_form.cleaned_data['priority']
        if priority:
            q = q.filter(priority=int(priority))

        # Filter: tags (select)
        tags = request.GET.get("TEMP_tags")
        if tags is not None:
            # TODO: does this work?
            q = q.filter(tags__in=tags.split(','))

        # Filter: folder (select) -- TODO, is this needed?

        # Filter: overdue (bool)
        overdue = filter_form.cleaned_data['overdue']
        if overdue:
            q = q.filter(due__lt=timezone.now(), done=False)

        # Filter: has_reminder (bool)
        has_reminder = filter_form.cleaned_data['has_reminder']
        if has_reminder:
            q = q.exclude(reminder=None)

        # Filter: has_reminder (bool)
        no_project = filter_form.cleaned_data['no_project']
        if no_project:
            q = q.filter(project=None)

        # Filter: pinned (bool)
        pinned = filter_form.cleaned_data['pinned']
        if pinned:
            q = q.filter(pinned=True)

        # TODO: filter due/reminder date range

        # Filter: projects (select)
        projects = request.GET.get("TEMP_projects")
        if projects is not None:
            # TODO: does this work?
            indexes = [int(i) for i in projects.split(',')]
            q = q.filter(project__in=indexes)

        # Search (TODO)
        search = filter_form.cleaned_data['search']
        if search:
            q = q.filter(title__icontains=search)

        return q

    def process_context(self, request, context):
        """Add new_location to the context."""
        context['new_location'] = self.new_location
        context['show_add_button'] = self.show_add_button


class AddView(View):
    """Addition view."""

    @method_decorator(login_required)
    def get(self, request):
        """Show the task addition form."""
        form = self.form(request.user)
        # prefill some values
        loc = request.GET.get('loc', '')
        if loc in ['inbox', 'tasks', 'trash']:
            form.initial['folder'] = loc
        elif loc.startswith('tag__'):
            form.initial['tags'] = loc.split('__')[1]
        elif loc.startswith('project__'):
            form.initial['folder'] = 'tasks'
            form.initial['project'] = loc.split('__')[1]
        return render(request, self.template, {"mode": "add", self.has_var: False, "form": form})

    @method_decorator(login_required)
    def post(self, request):
        """Add a task in the detailed view."""
        form = self.form(request.user, request.POST)
        if form.is_valid():
            i = form.save(commit=False)
            i.user = request.user
            i.save()
            form.save_m2m()
            return HttpResponseRedirect(i.get_absolute_url())
        else:
            return render(request, self.template, {"mode": "add", self.has_var: False, "form": form})

# List views (implement TaskListView)


def index(request):
    """Show the public index page or the dashboard."""
    if not request.user.is_authenticated():
        return render(request, "achieve/pub_index.html", {})
    else:
        inbox = queries.inbox(request).order_by('-due', '-added')
        pinned_tasks = queries.pinned_tasks_srp(request).order_by('title', '-due', '-added')
        due_soon = queries.due_soon(request).order_by('-due', '-added')
        context = {
            'inbox': inbox[:settings.ACHIEVE_ITEMS_PER_PAGE],
            'due_soon': due_soon[:settings.ACHIEVE_ITEMS_PER_PAGE],
            'pinned_index': pinned_tasks,
            'inbox_has_more': inbox.count() > settings.ACHIEVE_ITEMS_PER_PAGE,
            'due_soon_has_more': due_soon.count() > settings.ACHIEVE_ITEMS_PER_PAGE,
        }
        return render(request, "achieve/index.html", context)


class InboxView(TaskListView):
    """Display the inbox."""
    title = 'Inbox'
    query = staticmethod(queries.inbox)
    badge_name = 'inbox'
    empty_msg = "Hooray, the inbox is empty!"
    new_location = 'inbox'


class AllTasksView(TaskListView):
    """Display all tasks in existence."""
    title = 'All Tasks'
    query = staticmethod(queries.all_tasks)
    badge_name = 'all_tasks'
    empty_msg = "You have no tasks — time to add some!"


class TrashView(TaskListView):
    title = 'Trash'
    query = staticmethod(queries.trash)
    badge_name = 'trash'
    empty_msg = 'The trash is empty.'
    template = 'achieve/trash.html'
    show_add_button = False


class DueSoonView(TaskListView):
    """Display tasks that are due soon."""
    title = 'Due Soon'
    query = staticmethod(queries.due_soon)
    badge_name = 'due_soon'
    empty_msg = "Hooray, you have no tasks due soon!"


class ProjectsView(AchieveListView):
    """Display all projects in existence."""
    title = 'Projects'
    query = staticmethod(queries.projects)
    badge_name = 'projects'
    template = 'achieve/projects.html'
    filter_form = ProjectFilterForm
    default_sort = ('-open', '-added')
    sortable = (
        ('open', 'ps_open'),
        ('priority', 'ps_priority'),
        ('title', 'ps_title'),
    )

    def process_filters(self, request, args, kwargs, filter_form):
        """Process filters."""
        q = self.query(request, *args, **kwargs)
        # Filter: open (nullable bool)
        open = filter_form.cleaned_data['open']
        if open != '-1':
            q = q.filter(open=(open == '1'))

        # Filter: priority (int)
        priority = filter_form.cleaned_data['priority']
        if priority:
            q = q.filter(priority=int(priority))

        # Filter: progress
        progress_f = filter_form.cleaned_data['progress']
        if progress_f == '0':
            all_false = Project.objects.filter(task__done=False).exclude(task__done=True)
            empty = Project.objects.filter(task__isnull=True)
            q = (all_false | empty).distinct()
        elif progress_f == '50':
            q = Project.objects.filter(task__done=True).filter(task__done=False).distinct()
        elif progress_f == '100':
            q = Project.objects.filter(task__done=True).exclude(task__done=False).distinct()

        # Filter: pinned (bool)
        pinned = filter_form.cleaned_data['pinned']
        if pinned:
            q = q.filter(pinned=True)

        # Search (TODO)
        search = filter_form.cleaned_data['search']
        if search:
            q = q.filter(title__icontains=search)

        return q


class ProjectView(TaskListView):
    """Display a single project."""
    template = 'achieve/project_detail.html'
    empty_msg = 'This project is empty.'

    def query(self, request, slug):
        """Query the database for the project."""
        self.p = get_object_or_404(Project, slug=slug, user=request.user)
        return queries.tasks_in_project(request, self.p)

    def process_context(self, request, context):
        """Add project to context."""
        context['project'] = self.p
        self.new_location = 'project__{0}'.format(self.p.pk)
        super().process_context(request, context)

    def post(self, request, slug):
        """Handle POST requests."""
        self.query(request, slug)
        if request.POST.get('action') == 'delete':
            if request.POST.get('really') == '1':
                if request.POST.get('delete_tasks') == 'delete':
                    self.p.task_set.all().delete()
                elif request.POST.get('delete_tasks') == 'trash':
                    self.p.task_set.all().update(project=None, folder='trash')
                else:
                    self.p.task_set.clear()

                self.p.delete()
                update_badges(request.user)
                messages.success(request, "Project “{0}” deleted permanently.".format(self.p.title))
                return HttpResponseRedirect(reverse('achieve:projects'))
            elif request.POST.get('really') == '0':
                pass
            else:
                has_deletable = self.p.task_set.count() > 0

                context = {
                    'title': 'Delete project {0}'.format(self.p.title),
                    'question': 'Are you sure you want to delete this project?',
                    'type_yes': 'danger',
                    'type_no': 'default',
                    'delete_tasks_q': has_deletable,
                    'itemname': 'project',
                    'action': 'delete'
                }
                return render(request, "achieve/confirm.html", context)
        elif request.POST.get('action') == 'save':
            form = AddEditProjectForm(request.user, request.POST, instance=self.p)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(self.p.get_absolute_url())
            else:
                return render(request, "achieve/project_edit.html", {"mode": "edit", "has_project": True, "project": self.p, "form": form})
        elif request.POST.get('action') == 'edit':
            form = AddEditProjectForm(request.user, instance=self.p)
            return render(request, "achieve/project_edit.html", {"mode": "edit", "has_project": True, "project": self.p, "form": form})
        elif request.POST.get('action') == 'open':
            self.p.open = True
            messages.success(request, undo_btn("Project “{0}” opened.".format(self.p.title), "achieve:project", request, "close", slug=slug))
            self.p.save()
        elif request.POST.get('action') == 'close':
            self.p.open = False
            messages.success(request, undo_btn("Project “{0}” closed.".format(self.p.title), "achieve:project", request, "open", slug=slug))
            self.p.save()
        elif request.POST.get('action') == 'pin':
            self.p.pinned = True
            messages.success(request, undo_btn("Project “{0}” pinned.".format(self.p.title), "achieve:project", request, "unpin", slug=slug))
            self.p.save()
        elif request.POST.get('action') == 'pin':
            self.p.pinned = True
            messages.success(request, undo_btn("Project “{0}” pinned.".format(self.p.title), "achieve:project", request, "unpin", slug=slug))
            self.p.save()
        elif request.POST.get('action') == 'unpin':
            self.p.pinned = False
            messages.success(request, undo_btn("Project “{0}” unpinned.".format(self.p.title), "achieve:project", request, "pin", slug=slug))
            self.p.save()
        elif request.POST.get('action') == 'show':
            pass
        else:
            return render(request, "achieve/error.html", {"message": "Unknown action."}, status=400)

        if request.POST.get('next'):
            return next_page(request)
        else:
            return self.get(request, self.p.slug)


class TagProjectsView(ProjectsView):
    """Display projects with a tag."""
    badge_name = None

    @property
    def title(self):
        """Provide a title for the page."""
        return "{0} — Projects".format(self.t.title)

    def query(self, request, slug):
        """Query the database for a tag."""
        self.t = get_object_or_404(Tag, slug=slug, user=request.user)
        return queries.projects_with_tag(request, self.t)

    def process_context(self, request, context):
        """Provide a new task location for this page."""
        self.new_location = 'tag__{0}'.format(self.t.pk)
        context['new_location'] = self.new_location
        super().process_context(request, context)


class TagTasksView(TaskListView):
    @property
    def title(self):
        """Provide a title for the page."""
        return "{0} — Tasks".format(self.t.title)

    def query(self, request, slug):
        """Query the database for a tag."""
        self.t = get_object_or_404(Tag, slug=slug, user=request.user)
        return queries.tasks_with_tag(request, self.t)

    def process_context(self, request, context):
        """Provide a new task location for this page."""
        self.new_location = 'tag__{0}'.format(self.t.pk)
        super().process_context(request, context)


@login_required
def tags(request):
    """Display all tags in existence."""
    if request.method == "POST" and request.POST.get('action') == 'add':
        form = AddEditTagForm(request.POST)
        if form.is_valid():
            i = form.save(commit=False)
            i.user = request.user
            i.save()
            form.save_m2m()
            return HttpResponseRedirect(i.get_absolute_url())

    form = AddEditTagForm()

    tags = queries.tags(request)
    tags_per_letter_d = collections.defaultdict(list)
    for tag in tags:
        tags_per_letter_d[tag.title[0].upper()].append(tag)
    tags_per_letter_s = collections.OrderedDict()
    for letter, tpl in sorted(tags_per_letter_d.items()):
        tags_per_letter_s[letter] = tpl
    context = {
        'title': 'Tags',
        'tags_per_letter': tags_per_letter_s,
        'form': form,
    }
    return render(request, "achieve/tags.html", context)


@login_required
def templates(request):
    """Manage project templates."""
    raise NotImplementedError


@login_required
def reference(request):
    """Display Reference cabinet."""
    raise NotImplementedError

# Addition views (may implement AddView)


class AddTaskView(AddView):
    """Task addition view."""
    template = "achieve/task_edit.html"
    has_var = "has_task"
    form = AddEditTaskForm


class AddProjectView(AddView):
    """Project addition view."""
    template = "achieve/project_edit.html"
    has_var = "has_project"
    form = AddEditProjectForm


@login_required
def collection(request):
    """Add new tasks in bulk in collection mode."""
    if request.method == 'POST':
        tasks = []
        for i in request.POST['collection-box'].split('\n'):
            i = i.strip()
            if i:
                t = add_to_inbox(request, i, False)
                t.save()
                tasks.append(t)
        return render(request, "achieve/collection_results.html", {"tasks": tasks})
    else:
        return render(request, "achieve/collection.html", {})


@login_required
def quick_add(request):
    """Add one new task to the Inbox."""
    if request.method != 'POST':
        return render(request, "achieve/error.html", {"message": "Quick Add is only available via POST."}, status=400)
    elif 'title' not in request.POST:
        return render(request, "achieve/error.html", {"message": "No task title to add."}, status=400)

    title = request.POST['title'].strip()
    if title:
        task = add_to_inbox(request, title)
        messages.success(request, format_html('Task “<a href="{0}">{1}</a>” added.', task.get_absolute_url, task.title))
    else:
        return render(request, "achieve/error.html", {"message": "Task title is empty."}, status=400)
    return next_page(request)

# Actions


@login_required
def trash_empty(request):
    """Empty the Trash."""
    really = request.POST.get('really')
    if really == '1':
        queries.trash(request).delete()
        messages.success(request, "Trash emptied.")
        update_badges(request.user)
        return next_page(request, reverse('achieve:trash'))
    elif really == '0':
        return next_page(request, reverse('achieve:trash'))
    else:
        context = {
            'title': 'Empty Trash',
            'question': 'Are you sure you want to empty the trash?  All items will be irreversibly lost.',
            'type_yes': 'danger',
            'type_no': 'default'
        }
        return render(request, "achieve/confirm.html", context)


@login_required
def review(request):
    """Review progress."""
    raise NotImplementedError

# Singular entities


@login_required
def task(request, slug):
    """Display a single task."""
    t = get_object_or_404(Task, slug=slug, user=request.user)
    if request.method == 'POST':
        if request.POST.get('action') == 'done':
            t.done = True
            undo_name = 'undo'
            if t.folder == 'inbox':
                t.folder = 'tasks'
                undo_name = 'undo_inbox'
            t.save()
            messages.success(request, undo_btn("Task “{0}” marked as done!".format(t.title), "achieve:task", request, undo_name, slug=slug))
            return next_page(request)
        elif request.POST.get('action') in ('undo', 'undo_inbox'):
            t.done = False
            if request.POST.get('action') == 'undo_inbox':
                t.folder = 'inbox'  # special case: restore tasks to inbox on undo
            t.save()
            messages.success(request, undo_btn("Task “{0}” marked as not done.".format(t.title), "achieve:task", request, "done", slug=slug))
            return next_page(request)
        elif request.POST.get('action') == 'delete':
            t.folder = 'trash'
            t.save()
            messages.success(request, undo_btn("Task “{0}” moved to Trash.".format(t.title), "achieve:task", request, "undelete", slug=slug))
            return next_page(request)
        elif request.POST.get('action') == 'undelete':
            t.folder = 'inbox'
            t.save()
            messages.success(request, undo_btn("Task “{0}” moved to Inbox.".format(t.title), "achieve:task", request, "delete", slug=slug))
        elif request.POST.get('action') == 'move_inbox':
            t.folder = 'inbox'
            t.save()
            messages.success(request, undo_btn("Task “{0}” moved to Inbox.".format(t.title), "achieve:task", request, "move_tasks", slug=slug))
        elif request.POST.get('action') == 'move_tasks':
            t.folder = 'tasks'
            t.save()
            messages.success(request, undo_btn("Task “{0}” moved to Tasks.".format(t.title), "achieve:task", request, "move_inbox", slug=slug))
            return next_page(request)
        elif request.POST.get('action') == 'pin':
            t.pinned = True
            t.save()
            messages.success(request, undo_btn("Task “{0}” pinned.".format(t.title), "achieve:task", request, "unpin", slug=slug))
            return next_page(request)
        elif request.POST.get('action') == 'unpin':
            t.pinned = False
            t.save()
            messages.success(request, undo_btn("Task “{0}” unpinned.".format(t.title), "achieve:task", request, "pin", slug=slug))
            return next_page(request)
        elif request.POST.get('action') == 'perm_delete':
            t.delete()
            messages.success(request, "Task “{0}” deleted permanently.".format(t.title))
            return HttpResponseRedirect(reverse('achieve:index'))
        elif request.POST.get('action') == 'save':
            old_date = t.reminder
            form = AddEditTaskForm(request.user, request.POST, instance=t)
            if form.is_valid():
                t = form.save(commit=False)
                t.user = request.user
                if t.reminder != old_date:
                    t.reminder_seen = False
                t.save()
                form.save_m2m()
                return HttpResponseRedirect(t.get_absolute_url())
            else:
                return render(request, "achieve/task_edit.html", {"mode": "edit", "has_task": True, "task": t, "form": form})
        elif request.POST.get('action') == 'edit':
            form = AddEditTaskForm(request.user, instance=t)
            return render(request, "achieve/task_edit.html", {"mode": "edit", "has_task": True, "task": t, "form": form})
        elif request.POST.get('action') == 'show':
            pass
        else:
            return render(request, "achieve/error.html", {"message": "Unknown action."}, status=400)

    if request.GET.get('reminder_seen') == 'True':
        t.reminder_seen = True
        t.save()

    return render(request, "achieve/task_detail.html", {"task": t})


@login_required
def tag(request, slug):
    """Display a single tag."""
    tag = get_object_or_404(Tag, slug=slug, user=request.user)

    if request.method == "POST" and request.POST.get('action') == 'save':
        form = AddEditTagForm(request.POST, instance=tag)
        if form.is_valid():
            i = form.save(commit=False)
            i.user = request.user
            i.save()
            form.save_m2m()
            return HttpResponseRedirect(i.get_absolute_url())
    elif request.method == "POST" and request.POST.get('action') == 'pin':
        tag.pinned = True
        tag.save()
        messages.success(request, undo_btn("Tag “{0}” pinned.".format(tag.title), "achieve:tag", request, "unpin", slug=slug))
    elif request.method == "POST" and request.POST.get('action') == 'unpin':
        tag.pinned = False
        tag.save()
        messages.success(request, undo_btn("Tag “{0}” unpinned.".format(tag.title), "achieve:tag", request, "pin", slug=slug))

    form = AddEditTagForm(instance=tag)

    tasks = queries.tasks_with_tag(request, tag).order_by('done', '-due', '-added')
    projects = queries.projects_with_tag(request, tag).order_by('-added')
    context = {
        'title': tag.title,
        'tag': tag,
        'form': form,
        'tasks': tasks[:settings.ACHIEVE_ITEMS_PER_PAGE],
        'projects': projects[:settings.ACHIEVE_ITEMS_PER_PAGE],
        'tasks_has_more': tasks.count() > settings.ACHIEVE_ITEMS_PER_PAGE,
        'projects_has_more': projects.count() > settings.ACHIEVE_ITEMS_PER_PAGE,
        'empty_projects_msg': 'This tag has no projects.',
        'empty_tasks_msg': 'This tag has no tasks.',
    }

    return render(request, "achieve/tag_detail.html", context)


@login_required
def auth_profile(request):
    """Display the user profile page."""
    if request.method == "POST" and request.POST.get('action') == 'save':
        form = AchieveProfileForm(request.POST)
        if form.is_valid():
            request.user.email = form.cleaned_data['email']
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            # We need to validate timezones.
            try:
                tzname = form.cleaned_data['timezone']
                pytz.timezone(tzname)
                request.user.achieveprofile.timezone = tzname
                request.user.achieveprofile.save()
            except pytz.UnknownTimeZoneError:
                form.errors['timezone'] = 'Unknown time zone.'
            request.user.save()
    elif request.method == "POST" and request.POST.get('action') == 'update_badges':
        update_badges(request.user)
        messages.success(request, "Badges successfully updated.")

    if request.POST.get('action') != 'save':
        form = AchieveProfileForm()
        form.initial['email'] = request.user.email
        form.initial['first_name'] = request.user.first_name
        form.initial['last_name'] = request.user.last_name
        form.initial['timezone'] = request.user.achieveprofile.timezone

    return render(request, "achieve/auth_profile.html", {'form': form})


@login_required
def api_reminders_soon(request):
    """Return reminders due soon in JSON format."""
    q = queries.reminders_soon(request)
    data = []
    for task in q:
        data.append({
            'id': task.pk,
            'title': task.title,
            'timestamp': task.reminder.replace(tzinfo=pytz.UTC).timestamp(),
            'description': task.description,
            'url': task.get_absolute_url()
        })
    return JsonResponse({"reminders": data})
