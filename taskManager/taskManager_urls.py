from django.urls import re_path as url

from taskManager import views

urlpatterns = [
                       url(r'^$', views.index, name='index'),

                       # User details
                       url(r'^view_all_users/$',
                           views.view_all_users, name='view_all_users'),

                       # File
                       url(r'^download/(?P<file_id>\d+)/$',
                           views.download, name='download'),
                       url(r'^(?P<project_id>\d+)/upload/$',
                           views.upload, name='upload'),
                       url(r'^downloadprofilepic/(?P<user_id>\d+)/$',
                           views.download_profile_pic, name='download_profile_pic'),

                       # Authentication & Authorization
                       url(r'^register/$', views.register, name='register'),
                       url(r'^login/$', views.login, name='login'),
                       url(r'^logout/$', views.logout_view, name='logout'),
                       url(r'^manage_groups/$', views.manage_groups,
                           name='manage_groups'),
                       url(r'^profile/$', views.profile, name='profile'),
                       url(r'^change_password/$', views.change_password,
                           name='change_password'),
                      url(r'^forgot_password/$', views.forgot_password,
                           name='forgot_password'),
                      url(r'^reset_password/$', views.reset_password,
                           name='reset_password'),
                       url(r'^profile/(?P<user_id>\d+)$',
                           views.profile_by_id, name='profile_by_id'),
                       url(r'^profile_view/(?P<user_id>\d+)$',
                           views.profile_view, name='profile_view'),

                       # Projects
                       url(r'^project_create/$', views.project_create,
                           name='project_create'),
                       url(r'^(?P<project_id>\d+)/edit_project/$',
                           views.project_edit, name='project_edit'),
                       url(r'^manage_projects/$', views.manage_projects,
                           name='manage_projects'),
                       url(r'^(?P<project_id>\d+)/project_delete/$',
                           views.project_delete, name='project_delete'),
                       url(r'^(?P<project_id>.+)/project_details/$',
                           views.project_details, name='project_details'),
                       url(r'^project_list/$', views.project_list,
                           name='project_list'),

                       # Tasks
                       url(r'^(?P<project_id>\d+)/task_create/$',
                           views.task_create, name='task_create'),
                       url(r'^(?P<project_id>\d+)/(?P<task_id>\d+)/$',
                           views.task_details, name='task_details'),
                       url(r'^(?P<project_id>\d+)/task_edit/(?P<task_id>\d+)$',
                           views.task_edit, name='task_edit'),
                       url(r'^(?P<project_id>\d+)/task_delete/(?P<task_id>\d+)$',
                           views.task_delete, name='task_delete'),
                       url(r'^(?P<project_id>\d+)/task_complete/(?P<task_id>\d+)$',
                           views.task_complete, name='task_complete'),
                       url(r'^task_list/$', views.task_list, name='task_list'),
                       url(r'^(?P<project_id>\d+)/manage_tasks/$',
                           views.manage_tasks, name='manage_tasks'),


                       # Notes
                       url(r'^(?P<project_id>\d+)/(?P<task_id>\d+)/note_create/$',
                           views.note_create, name='note_create'),
                       url(r'^(?P<project_id>\d+)/(?P<task_id>\d+)/note_edit/(?P<note_id>\d+)$',
                           views.note_edit, name='note_edit'),
                       url(r'^(?P<project_id>\d+)/(?P<task_id>\d+)/note_delete/(?P<note_id>\d+)$',
                           views.note_delete, name='note_delete'),

                       url(r'^dashboard/$', views.dashboard, name='dashboard'),
                       url(r'^search/$', views.search, name='search'),

                       # Settings - DEBUG
                       url(r'^settings/$', views.tm_settings, name='settings'),
                       url(r'^view_img/$', views.view_img, name='view_img'),
                       url(r'^ping/$', views.ping, name='ping'),
                      ]
