# Vulnerable Task Manager

from django.urls import include, re_path as url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.conf import settings
from django.views.defaults import page_not_found
from django.conf.urls.static import static

from rest_framework import routers
from rest_framework.authtoken import views
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from taskManager.serializers import UserViewSet, UserProfileViewSet, TaskViewSet, ProjectViewSet, NotesViewSet, FileViewSet

from taskManager.views import index

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'userprofiles', UserProfileViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'notes', NotesViewSet)
router.register(r'files', FileViewSet)

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^taskManager/', include(('taskManager.taskManager_urls','taskManager'), namespace="taskManager")),
    url(r'^admin/', admin.site.urls ),
    url(r'^ht/', include('health_check.urls')),
    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api-token/', views.obtain_auth_token),
    url(r'^schema/', SpectacularAPIView.as_view(), name='schema'),
    url(r'^swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    url(r'^redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
   ]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)