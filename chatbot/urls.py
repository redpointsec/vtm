from django.urls import re_path as url
from chatbot import views

urlpatterns = [
    url(r'^page/$', views.chat_page, name='chat_page'),
    url(r'^stream/$', views.chat_stream, name='chat_stream'),
    url(r'^send/$', views.chat_send, name='chat_send'),
    url(r'^sessions/$', views.session_list, name='session_list'),
    url(r'^session/(?P<pk>[^/]+)/messages/$', views.session_messages, name='session_messages'),
    url(r'^session/new/$', views.session_new, name='session_new'),
    url(r'^session/(?P<pk>[^/]+)/delete/$', views.session_delete, name='session_delete'),
]
