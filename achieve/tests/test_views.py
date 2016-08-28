"""Achieve view tests."""

import datetime
import json
import pytest
import pytz
from achieve.models import Task
from django.utils import timezone


@pytest.mark.django_db
def test_index_anonymous(client):
    request = client.get("/")
    assert request.status_code == 200


@pytest.mark.django_db
def test_index_admin(admin_client):
    request = admin_client.get("/")
    assert request.status_code == 200


def _make_tasklist_task(user, tid, folder='inbox', done=False):
    t = Task()
    t.user = user
    t.title = "TLT" + str(tid)
    t.folder = folder
    t.done = done
    t.save()
    return t


def _test_patterns(html, *tasks):
    for i, t in enumerate(tasks, 1):
        if t:
            assert "TLT{0}".format(i).encode('ascii') in html
        else:
            assert "TLT{0}".format(i).encode('ascii') not in html


@pytest.mark.django_db
def test_tasklist(admin_user, admin_client):
    """This tests multiple task lists."""
    tasks = [
        _make_tasklist_task(admin_user, 1, "inbox"),
        _make_tasklist_task(admin_user, 2, "inbox", True),
        _make_tasklist_task(admin_user, 3, "tasks"),
        _make_tasklist_task(admin_user, 4, "tasks", True),
        _make_tasklist_task(admin_user, 5, "trash"),
        _make_tasklist_task(admin_user, 6, "trash", True),
    ]

    # InboxView: sees only t1 and t2
    request = admin_client.get("/inbox/")
    assert request.status_code == 200
    _test_patterns(request.content, True, True, False, False, False, False)

    # AllTasksView: sees t1, t2, t3, t4
    request = admin_client.get("/tasks/")
    assert request.status_code == 200
    _test_patterns(request.content, True, True, True, True, False, False)

    # TrashView: sees only t5 and t6
    request = admin_client.get("/trash/")
    assert request.status_code == 200
    _test_patterns(request.content, False, False, False, False, True, True)

    # InboxView, filtered done only: sees only t2
    request = admin_client.get("/inbox/?f-done=1")
    assert request.status_code == 200
    _test_patterns(request.content, False, True, False, False, False, False)

    # InboxView, filtered undone only: sees only t1
    request = admin_client.get("/inbox/?f-done=0")
    assert request.status_code == 200
    _test_patterns(request.content, True, False, False, False, False, False)

    for t in tasks:
        t.delete()


@pytest.mark.django_db
def test_reminders_soon(admin_user, admin_client):
    title = "ReminderTest"
    reminder = timezone.now() + datetime.timedelta(seconds=1000)
    description = "Reminder test!"

    t = Task()
    t.user = admin_user
    t.title = title
    t.description = description
    t.reminder = reminder
    t.save()

    request = admin_client.get("/api/reminders/soon/")
    assert request.status_code == 200
    data = json.loads(request.content.decode('utf-8'))

    assert len(data) == 1
    assert len(data['reminders']) == 1
    assert data['reminders'][0]['id'] == t.pk
    assert data['reminders'][0]['title'] == title
    assert data['reminders'][0]['description'] == description
    assert data['reminders'][0]['url'] == t.get_absolute_url()
    timestamp = datetime.datetime.utcfromtimestamp(
        data['reminders'][0]['timestamp']).replace(tzinfo=pytz.UTC)
    assert timestamp == reminder

    # Delete reminder, try again
    t.reminder = None
    t.save()

    request = admin_client.get("/api/reminders/soon/")
    assert request.status_code == 200
    data = json.loads(request.content.decode('utf-8'))

    assert len(data) == 1
    assert len(data['reminders']) == 0

    t.delete()
