# Vulnerable Task Manager

from django.conf.urls import include, url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.conf import settings
from django.views.defaults import page_not_found

from taskManager.views import index

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^taskManager/', include(('taskManager.taskManager_urls','taskManager'), namespace="taskManager")),
    url(r'^admin/', admin.site.urls ),
   ]
