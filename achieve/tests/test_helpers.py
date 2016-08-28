"""Achieve helper tests."""

from achieve import models, helpers
from django.core.urlresolvers import reverse
import pytest


def test_get_next(rf):
    url_n = "http://example.com/"
    url_g = "http://example.org/"
    n = rf.post("/", {"next": url_n})
    g = rf.post("/")

    assert helpers.get_next(n, url_g) == url_n
    assert helpers.get_next(g, url_g) == url_g
    assert helpers.get_next(g) == reverse("achieve:index")


def test_next_page(rf):
    url_n = "http://example.com/"
    url_g = "http://example.org/"
    n = rf.post("/", {"next": url_n})
    g = rf.post("/")

    response_n = helpers.next_page(n, url_g)
    response_g = helpers.next_page(g, url_g)

    assert response_n.status_code == 302
    assert response_g.status_code == 302
    assert response_n.url == url_n
    assert response_g.url == url_g


def test_undo_btn(rf):
    url_next = "http://example.com/"
    request = rf.post("/", {"next": url_next})

    b = helpers.undo_btn("Undo text", "achieve:index", request, "TestAction")
    assert "Undo text" in b
    assert reverse("achieve:index") in b
    assert "TestAction" in b
    assert "csrf" in b


@pytest.mark.django_db
def test_add_to_inbox(admin_client):
    request = admin_client.post("/").wsgi_request
    title = "Hello!"
    title2 = "Hello!!"
    t1 = helpers.add_to_inbox(request, title, True)
    assert t1.title == title
    assert t1.folder == 'inbox'
    assert t1.slug == 'hello'
    assert t1.user == request.user
    assert t1.pk
    t2 = helpers.add_to_inbox(request, title2, False)
    assert t2.title == title2
    assert t2.folder == 'inbox'
    assert t2.slug == ''  # slugs are created on save
    assert t2.user == request.user
    assert t2.pk is None

    t2.save()
    assert t2.slug == 'hello-1'
    assert t2.pk
    t1.delete()
    t2.delete()


@pytest.mark.django_db
def test_update_slug(admin_user):
    tag1 = models.Tag()
    tag2 = models.Tag()
    tag3 = models.Tag()
    tag4 = models.Tag()

    tag1.title = tag3.title = tag4.title = "Foo"
    tag2.title = "Bar"

    tag1.user = tag2.user = tag3.user = tag4.user = admin_user

    tag1.save()
    tag2.save()
    tag3.save()
    tag4.save()

    assert tag1.slug == 'foo'
    assert tag1.slug == tag1.slugbase
    assert tag1.slugbase == tag3.slugbase == tag4.slugbase
    assert tag2.slug == 'bar'
    assert tag3.slug == 'foo-1'
    assert tag4.slug == 'foo-2'

    # Recalculation test
    helpers.update_slug(tag1, force=False, save=False)
    assert tag1.slug == 'foo'
    helpers.update_slug(tag1, force=True, save=False)
    assert tag1.slug == 'foo-3'
    helpers.update_slug(tag2, force=True, save=True)
    assert tag2.slug == 'bar'

    for tag in (tag1, tag2, tag3, tag4):
        tag.delete()


def test_process_sorting(admin_user, rf):
    sortable = (
        ('done', 's_done'),
        ('title', 's_title'),
    )
    default = ('done', 'title')
    desc = 'process_sorting'

    request = rf.get('/inbox')
    request.user = admin_user
    request.GET = request.GET.copy()

    t1 = helpers.add_to_inbox(request, "sort1", False)
    t1.description = desc
    t1.save()

    t2 = helpers.add_to_inbox(request, "sort2", False)
    t2.done = True
    t2.description = desc
    t2.save()

    t3 = helpers.add_to_inbox(request, "sort3", False)
    t3.done = True
    t3.description = desc
    t3.save()

    q = models.Task.objects.filter(description=desc)

    # Request 1: use default
    table = helpers.process_sorting(request, q, sortable, default)
    assert list(table) == [t1, t2, t3]

    # Request 2: done descending
    request.GET['s_done'] = 'desc'
    table = helpers.process_sorting(request, q, sortable, default)
    assert list(table) == [t2, t3, t1]

    # Request 3: done ascending, title descending
    request.GET['s_done'] = 'asc'
    request.GET['s_title'] = 'desc'
    table = helpers.process_sorting(request, q, sortable, default)
    assert list(table) == [t1, t3, t2]

    for t in (t1, t2, t3):
        t.delete()


def test_process_pagination(settings, admin_user, rf):
    request = rf.get('/inbox')
    request.user = admin_user
    request.GET = request.GET.copy()
    desc = "process_pagination"

    t1 = helpers.add_to_inbox(request, "pag1", False)
    t1.description = desc
    t1.save()

    t2 = helpers.add_to_inbox(request, "pag2", False)
    t2.description = desc
    t2.save()

    t3 = helpers.add_to_inbox(request, "pag3", False)
    t3.description = desc
    t3.save()

    q = models.Task.objects.filter(description=desc)

    settings.ACHIEVE_ITEMS_PER_PAGE = 2
    request.GET['page'] = 'foo'
    pfoo = helpers.process_pagination(request, q)
    request.GET['page'] = '1'
    p1 = helpers.process_pagination(request, q)
    request.GET['page'] = '2'
    p2 = helpers.process_pagination(request, q)
    request.GET['page'] = '3'
    p3 = helpers.process_pagination(request, q)

    assert list(p1) == [t1, t2]
    assert list(p2) == [t3]
    assert list(p3) == list(p2)
    assert list(pfoo) == list(p1)

    for t in (t1, t2, t3):
        t.delete()
