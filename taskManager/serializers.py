from rest_framework import serializers, viewsets
from django.contrib.auth.models import User
from taskManager.models import Task, Project, Notes, File, UserProfile
from drf_spectacular.utils import extend_schema_view, extend_schema
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters

# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff', 'is_superuser')

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(username=user.username)

class TaskSerializer(serializers.HyperlinkedModelSerializer):
    options = serializers.HyperlinkedRelatedField(
    view_name='task-detail',
    lookup_field = 'uuid',
    many=True,
    read_only=True)

    class Meta:
        model = Task
        fields = ('url', 'uuid', 'title', 'text', 'start_date', 'due_date', 'completed', 'project', 'users_assigned', 'options')
        lookup_field = 'uuid'
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'},
            'project': {'lookup_field': 'uuid'}
        }

class TaskFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='icontains')
    text = filters.CharFilter(lookup_expr='icontains')
    start_date = filters.DateFilter()
    due_date = filters.DateFilter()
    completed = filters.BooleanFilter()
    project = filters.CharFilter(lookup_expr='icontains')
    users_assigned = filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Task
        fields = ['title', 'text', 'start_date', 'due_date', 'completed', 'project', 'users_assigned']

class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Task.objects.all()
        return Task.objects.filter(users_assigned__in=[user])

class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Project
        fields = ('uuid', 'url', 'title', 'text', 'start_date', 'due_date', 'priority', 'users_assigned')
        lookup_field = 'uuid'
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'}
        }

class ProjectFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='icontains')
    text = filters.CharFilter(lookup_expr='icontains')
    start_date = filters.DateFilter()
    due_date = filters.DateFilter()
    priority = filters.NumberFilter()
    users_assigned = filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Project
        fields = ['title', 'text', 'start_date', 'due_date', 'priority', 'users_assigned']

class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProjectSerializer
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProjectFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Project.objects.all()
        return Project.objects.filter(users_assigned__in=[user])
    
    queryset = Project.objects.all()

class NotesSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Notes
        fields = ('uuid', 'title', 'text', 'image', 'user', 'task')
        lookup_field = 'uuid'
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'},
            'task': {'lookup_field': 'uuid'}
        }

class NotesFilter(filters.FilterSet):
    text = filters.CharFilter(lookup_expr='icontains')
    title = filters.CharFilter(lookup_expr='icontains')
    user = filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Notes
        fields = ['title', 'text', 'user']

class NotesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notes.objects.all()
    serializer_class = NotesSerializer
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend]
    filterset_class = NotesFilter

class FileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = File
        fields = ('uuid', 'name', 'path', 'project')
        lookup_field = 'uuid'
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'},
            'project': {'lookup_field': 'uuid'}
        }

class FileFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    path = filters.CharFilter(lookup_expr='icontains')
    project = filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = File
        fields = ['name', 'path', 'project']

class FileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend]
    filterset_class = FileFilter

class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('uuid', 'image', 'reset_token', 'reset_token_expiration', 'dob', 'ssn', 'user')
        lookup_field = 'uuid'
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'}
        }

class UserProfileFilter(filters.FilterSet):
    dob = filters.DateFilter()
    ssn = filters.CharFilter(lookup_expr='icontains')
    user = filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = UserProfile
        fields = ['dob', 'ssn', 'user']
        lookup_field = 'uuid'
        extra_kwargs = {
            'url': {'lookup_field': 'uuid'}
        }

class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserProfileFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=user)
