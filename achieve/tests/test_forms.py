"""Achieve form tests."""

import pytest
import random
from achieve.models import Project
from achieve import forms


def test_splitdatetime():
    sdt = forms.SplitDateTime()
    w = sdt.render('sdt_test', None)
    assert 'fa-calendar' in w
    assert 'form-control' in w
    assert 'datepicker' in w
    assert 'type="time"' in w


@pytest.mark.django_db
def test_addedittaskform(admin_user, django_user_model):
    title = "Project{0}Project".format(random.randint(1, 100))
    title2 = "Other{0}Other".format(random.randint(1, 100))

    p1 = Project()
    p1.title = title
    p1.user = admin_user
    p1.save()

    tu = django_user_model()
    tu.save()
    p2 = Project()
    p2.title = title2
    p2.user = tu
    p2.save()

    f = forms.AddEditTaskForm(admin_user)
    out = str(f)
    assert title in out
    assert title2 not in out
    assert 'task-title-editbox' in out
    assert 'fa-calendar' in out

    f = forms.AddEditTaskForm(tu)
    out = str(f)
    assert title not in out
    assert title2 in out
    assert 'task-title-editbox' in out
    assert 'fa-calendar' in out

    p1.delete()
    p2.delete()
    tu.delete()


@pytest.mark.django_db
def test_addeditprojectform(admin_user):
    f = forms.AddEditProjectForm(admin_user)
    assert 'project-title-editbox' in str(f)


def test_taskfilterform():
    f = forms.TaskFilterForm({})
    assert f.is_valid()
    assert f.cleaned_data['done'] == '-1'
    f = forms.TaskFilterForm({'f-done': '-1'})
    assert f.is_valid()
    assert f.cleaned_data['done'] == '-1'
    f = forms.TaskFilterForm({'f-done': '1'})
    assert f.is_valid()
    assert f.cleaned_data['done'] == '1'
    f = forms.TaskFilterForm({'f-done': '0'})
    assert f.is_valid()
    assert f.cleaned_data['done'] == '0'

    # The f- in front is significant -- in this case, 0 is ignored
    f = forms.TaskFilterForm({'done': '0'})
    assert f.is_valid()
    assert f.cleaned_data['done'] == '-1'


def test_projectfilterform():
    f = forms.ProjectFilterForm({})
    assert f.is_valid()
    assert f.cleaned_data['open'] == '-1'
    assert f.cleaned_data['progress'] == '-1'

    f = forms.ProjectFilterForm({'pf-open': '-1'})
    assert f.is_valid()
    assert f.cleaned_data['open'] == '-1'
    f = forms.ProjectFilterForm({'pf-open': '1'})
    assert f.is_valid()
    assert f.cleaned_data['open'] == '1'
    f = forms.ProjectFilterForm({'pf-open': '0'})
    assert f.is_valid()
    assert f.cleaned_data['open'] == '0'
    assert f.cleaned_data['progress'] == '-1'

    f = forms.ProjectFilterForm({'pf-progress': '-1'})
    assert f.is_valid()
    assert f.cleaned_data['progress'] == '-1'
    f = forms.ProjectFilterForm({'pf-progress': '0'})
    assert f.is_valid()
    assert f.cleaned_data['progress'] == '0'
    assert f.cleaned_data['open'] == '-1'
    f = forms.ProjectFilterForm({'pf-progress': '50'})
    assert f.is_valid()
    assert f.cleaned_data['progress'] == '50'
    f = forms.ProjectFilterForm({'pf-progress': '100'})
    assert f.is_valid()
    assert f.cleaned_data['progress'] == '100'

    # The pf- in front is significant
    f = forms.ProjectFilterForm({'progress': '100', 'open': '1'})
    assert f.is_valid()
    assert f.cleaned_data['progress'] == '-1'
    assert f.cleaned_data['open'] == '-1'
    # and it cannot be f- either
    f = forms.ProjectFilterForm({'f-progress': '50', 'f-open': '0'})
    assert f.is_valid()
    assert f.cleaned_data['progress'] == '-1'
    assert f.cleaned_data['open'] == '-1'


def test_achieveprofileform():
    f = forms.AchieveProfileForm()
    assert 'form-control' in str(f)
