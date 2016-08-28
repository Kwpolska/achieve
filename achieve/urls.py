"""URL patterns for Achieve."""
from achieve import views
from django.conf.urls import url

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^profile/$', views.auth_profile, name='auth_profile'),
    url(r'^quick_add/$', views.quick_add, name='quick_add'),
    url(r'^add/$', views.AddTaskView.as_view(), name='add'),
    url(r'^collection/$', views.collection, name='collection'),
    url(r'^tags/$', views.tags, name='tags'),
    url(r'^tag/(?P<slug>[a-zA-Z0-9-_]+)/$', views.tag, name='tag'),
    url(r'^tag/(?P<slug>[a-zA-Z0-9-_]+)/projects/$', views.TagProjectsView.as_view(), name='projects_with_tag'),
    url(r'^tag/(?P<slug>[a-zA-Z0-9-_]+)/tasks/$', views.TagTasksView.as_view(), name='tasks_with_tag'),
    url(r'^projects/$', views.ProjectsView.as_view(), name='projects'),
    url(r'^projects/add/$', views.AddProjectView.as_view(), name='project_add'),
    url(r'^project/(?P<slug>[a-zA-Z0-9-_]+)/$', views.ProjectView.as_view(), name='project'),
    url(r'^tasks/$', views.AllTasksView.as_view(), name='tasks'),
    url(r'^task/(?P<slug>[a-zA-Z0-9-_]+)/$', views.task, name='task'),
    url(r'^inbox/$', views.InboxView.as_view(), name='inbox'),
    url(r'^soon/$', views.DueSoonView.as_view(), name='due_soon'),
    url(r'^trash/$', views.TrashView.as_view(), name='trash'),
    url(r'^trash/empty/$', views.trash_empty, name='trash_empty'),
    url(r'^api/reminders/soon/$', views.api_reminders_soon, name='reminders_soon'),
]
