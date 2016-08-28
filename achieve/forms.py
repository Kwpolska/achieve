"""Forms for Achieve."""

from django import forms
from achieve.models import Task, Project, Tag
from django.utils.html import format_html

TInput = forms.TextInput(attrs={'class': 'form-control'})
TArea = forms.Textarea(attrs={'class': 'form-control'})
NPField = forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})


class SplitDateTime(forms.SplitDateTimeWidget):
    """A SplitDateTime Widget that has some specific styling."""

    def __init__(self, attrs=None):
        date = forms.TextInput(attrs={'class': 'form-control datepicker'})
        time = forms.TextInput(attrs={'class': 'form-control timepicker'})
        time.input_type = 'time'
        widgets = [date, time]
        # Note that we're calling MultiWidget, not SplitDateTimeWidget, because
        # we want to define widgets.
        forms.MultiWidget.__init__(self, widgets, attrs)

    def format_output(self, rendered_widgets):
        """Output the widget."""
        return format_html('<i class="fa fa-calendar"></i> {0} <i class="fa fa-clock-o"></i> {1}',
                           rendered_widgets[0], rendered_widgets[1])


class AddEditTaskForm(forms.ModelForm):
    """A form used to add and edit tasks."""

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(user=self.user)
        self.fields['tags'].queryset = Tag.objects.filter(user=self.user)

    class Meta:
        """Meta information for this form."""
        model = Task
        fields = ['title', 'done', 'priority', 'due', 'reminder', 'project', 'tags', 'folder', 'description', 'resolution', 'pinned']
        field_classes = {
            'due': forms.SplitDateTimeField,
            'reminder': forms.SplitDateTimeField,
        }

        SelectF = forms.Select(attrs={'class': 'form-control'})
        SelectP = forms.Select(attrs={'class': 'form-control'})
        SelectT = forms.SelectMultiple(attrs={'class': 'form-control'})
        widgets = {
            'title': forms.TextInput(attrs={'class': 'task-title-editbox form-control'}),
            'done': forms.CheckboxInput(attrs={'class': 'done-checkbox'}),
            'priority': NPField,
            'due': SplitDateTime,
            'reminder': SplitDateTime,
            'folder': SelectF,
            'project': SelectP,
            'tags': SelectT,
            'description': TArea,
            'resolution': TArea,
        }


class AddEditProjectForm(forms.ModelForm):
    """A form used to add projects."""

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['tags'].queryset = Tag.objects.filter(user=self.user)

    class Meta:
        """Meta information for this form."""
        model = Project
        fields = ['title', 'priority', 'tags', 'description', 'open', 'pinned']

        SelectT = forms.SelectMultiple(attrs={'class': 'form-control'})
        widgets = {
            'title': forms.TextInput(attrs={'class': 'project-title-editbox form-control'}),
            'priority': NPField,
            'tags': SelectT,
            'description': TArea,
        }


class AddEditTagForm(forms.ModelForm):
    """A form used to add tags."""

    class Meta:
        """Meta information for this form."""
        model = Tag
        fields = ['title', 'pinned']

        labels = {
            'title': 'Name'
        }

        widgets = {
            'title': TInput
        }


class TaskFilterForm(forms.Form):
    """A form used to filter tasks."""
    prefix = "f"
    done = forms.ChoiceField(
        (
            ("-1", "---"),
            ("1", "Done only"),
            ("0", "Pending only")
        ), initial="-1", required=False,
        widget=forms.Select(attrs={'class': 'form-control'}))
    priority = forms.IntegerField(
        required=False, widget=forms.TextInput(
            attrs={'class': 'form-control', 'type': 'number', 'min': '1'}))
    overdue = forms.BooleanField(required=False)
    has_reminder = forms.BooleanField(required=False)
    no_project = forms.BooleanField(required=False)
    pinned = forms.BooleanField(required=False)
    search = forms.CharField(
        required=False, widget=forms.TextInput(
            attrs={'class': 'form-control', 'type': 'search', 'placeholder': 'Search'}))

    # page is added in HTML

    def clean_done(self):
        if not self['done'].html_name in self.data:
            return self.fields['done'].initial
        return self.cleaned_data['done']


class ProjectFilterForm(forms.Form):
    """A form used to filter projects."""
    prefix = "pf"
    open = forms.ChoiceField(
        (
            ("-1", "---"),
            ("1", "Open only"),
            ("0", "Closed only"),
        ), initial="-1", required=False,
        widget=forms.Select(attrs={'class': 'form-control'}))
    progress = forms.ChoiceField(
        (
            ("-1", "---"),
            ("0", "Not started"),
            ("50", "In progress"),
            ("100", "Completed")
        ), initial="-1", required=False,
        widget=forms.Select(attrs={'class': 'form-control'}))
    priority = forms.IntegerField(
        required=False, widget=forms.TextInput(
            attrs={'class': 'form-control', 'type': 'number', 'min': '1'}))
    search = forms.CharField(
        required=False, widget=forms.TextInput(
            attrs={'class': 'form-control', 'type': 'search', 'placeholder': 'Search'}))
    pinned = forms.BooleanField(required=False)

    def clean_open(self):
        if not self['open'].html_name in self.data:
            return self.fields['open'].initial
        return self.cleaned_data['open']

    def clean_progress(self):
        if not self['progress'].html_name in self.data:
            return self.fields['progress'].initial
        return self.cleaned_data['progress']


class AchieveProfileForm(forms.Form):
    """Achieve Profile edit form."""
    first_name = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control'}))
    timezone = forms.CharField(
        label='Time zone', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'class': 'form-control', 'type': 'email'}))
