"""Models for Achieve."""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from django.utils.html import mark_safe, format_html
import markdown
import bleach

ALLOWED_TAGS = bleach.ALLOWED_TAGS + ['br', 'p', 'abbr', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'code', 's']
ALLOWED_ATTRIBUTES = bleach.ALLOWED_ATTRIBUTES.copy()
ALLOWED_ATTRIBUTES['img'] = ['src', 'alt', 'title']
MD_EXTENSIONS = ['markdown.extensions.abbr', 'markdown.extensions.smart_strong', 'markdown.extensions.nl2br', 'mdx_linkify', 'markdown.extensions.toc']


class Tag(models.Model):
    """A tag that can be attached to Tasks and Projects."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    slugbase = models.SlugField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pinned = models.BooleanField(default=False)

    def __str__(self):
        """Return the name of a tag."""
        return self.title

    def get_absolute_url(self):
        """Get the absolute URL of a tag."""
        return reverse("achieve:tag", args=(self.slug,))

    def link(self):
        """Produce a HTML link to a tag."""
        return format_html('<a href="{0}">{1}</a>', self.get_absolute_url(), self.title)

    def link_label(self):
        """Produce a HTML link to a tag, with label styling."""
        return format_html('<a href="{0}" class="label label-default tag">{1}</a>', self.get_absolute_url(), self.title)


class Project(models.Model):
    """A project, which organizes multiple tasks with a common goal."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    slugbase = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.PositiveSmallIntegerField(default=1, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    added = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    open = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pinned = models.BooleanField(default=False)

    def __str__(self):
        """Return the title of a project."""
        return self.title

    def get_absolute_url(self):
        """Get the absolute URL of a project."""
        return reverse("achieve:project", args=(self.slug,))

    def link(self):
        """Produce a HTML link to a project."""
        return format_html('<a href="{0}">{1}</a>', self.get_absolute_url(), self.title)

    def progress(self):
        """Return a two-tuple of (done tasks, all tasks) in a project."""
        t = self.task_set
        return (t.filter(done=True).count(), t.count())

    def description_md(self):
        """Return Markdown-formatted description."""
        if self.description.strip():
            return mark_safe(bleach.clean(markdown.markdown(self.description, extensions=MD_EXTENSIONS),
                                          tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES))
        else:
            return ''

    def progressbar(self):
        """Make a pretty progressbar."""
        v, m = self.progress()
        try:
            perc = 100 * v / m
        except ZeroDivisionError:
            perc = 0
        pf = "{0:0.0f}".format(perc)  # hack for django
        return format_html('<div class="progress"><div class="progress-bar" role="progressbar" aria-valuenow="{0}" aria-valuemin="0" aria-valuemax="{1}" style="width: {2}%">{3}% ({0}/{1})</div></div>', v, m, perc, pf)


class Task(models.Model):
    """A task, the most basic unit of productivity."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    slugbase = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    resolution = models.TextField(blank=True)
    project = models.ForeignKey(Project, blank=True, null=True, on_delete=models.SET_NULL)
    priority = models.PositiveSmallIntegerField(default=1, blank=True)
    done = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.CharField(max_length=10, default='inbox', choices=(
        ('inbox', 'Inbox'),
        ('tasks', 'Tasks'),
        ('trash', 'Trash')
    ))
    due = models.DateTimeField(null=True, blank=True)
    added = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    reminder = models.DateTimeField(null=True, blank=True)
    reminder_seen = models.BooleanField(default=False)
    pinned = models.BooleanField(default=False)

    def __str__(self):
        """Return the title of a task."""
        return self.title

    def get_absolute_url(self):
        """Get the absolute URL of a task."""
        return reverse("achieve:task", args=(self.slug,))

    def overdue(self):
        """Check if the task is overdue."""
        if self.done:
            return False
        elif self.due is not None:
            return self.due <= timezone.now()
        else:
            return False

    def description_md(self):
        """Return Markdown-formatted description."""
        if self.description.strip():
            return mark_safe(bleach.clean(markdown.markdown(self.description, extensions=MD_EXTENSIONS),
                                          tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES))
        else:
            return mark_safe('<p class="text-muted">No description provided.</p>')

    def resolution_md(self):
        """Return Markdown-formatted resolution information."""
        if self.resolution.strip():
            return mark_safe(bleach.clean(markdown.markdown(self.resolution, extensions=MD_EXTENSIONS),
                                          tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES))
        else:
            return ''


class AchieveProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    timezone = models.CharField(max_length=100, default="UTC")
    badge_inbox = models.IntegerField(default=0)
    badge_all_tasks = models.IntegerField(default=0)
    badge_trash = models.IntegerField(default=0)
    badge_projects = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Achieve Profile"
        verbose_name_plural = "Achieve Profiles"

    def __str__(self):
        return self.user.username

# Signal handlers (slug and badge updating)
import achieve.helpers  # NOQA
import achieve.queries  # NOQA


@receiver(models.signals.pre_save, sender=Tag)
@receiver(models.signals.pre_save, sender=Project)
@receiver(models.signals.pre_save, sender=Task)
def update_slug_on_save(sender, **kwargs):
    """Update slugs when an object is saved."""
    achieve.helpers.update_slug(kwargs['instance'], save=False)


@receiver(models.signals.post_save, sender=Task)
@receiver(models.signals.post_save, sender=Project)
def update_badges_on_save(sender, instance, created, **kwargs):
    """Update badges when a Task/Project is saved."""
    achieve.helpers.update_badges(instance.user)


@receiver(models.signals.post_save, sender=settings.AUTH_USER_MODEL)
def user_post_save_receiver(sender, instance, created, **kwargs):
    """Create a profile for an user if one is not found already."""
    try:
        instance.achieveprofile
    except models.ObjectDoesNotExist:
        p = AchieveProfile()
        p.user = instance
        p.save()
