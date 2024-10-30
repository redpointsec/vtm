from rest_framework import routers, serializers, viewsets
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
    class Meta:
        model = Task
        fields = ('uuid','url', 'title', 'text', 'start_date', 'due_date', 'completed', 'project', 'users_assigned')

class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Task.objects.all()
        return Task.objects.filter(users_assigned__in=[user])

class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Project
        fields = ('uuid','url', 'title', 'text', 'start_date', 'due_date', 'priority', 'users_assigned')

class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProjectSerializer

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

class NotesFilter(filters.FilterSet):
    text = filters.CharFilter(lookup_expr='icontains')
    title = filters.CharFilter(lookup_expr='icontains')
    user = filters.CharFilter(lookup_expr='icontains')
    task = filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Notes
        fields = ['title', 'text', 'user', 'task']

class NotesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notes.objects.all()
    serializer_class = NotesSerializer
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend]
    filterset_class = NotesFilter

    #def get_queryset(self):
        # Filter by query parameters
    #    uuid = self.request.query_params.get('uuid')
    #    if uuid:
    #        return Notes.objects.filter(uuid=uuid)
    #    return Notes.objects.all()

class FileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = File
        fields = ('uuid','url', 'name', 'path', 'project')

class FileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer

class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('uuid','url', 'image', 'reset_token', 'reset_token_expiration', 'dob', 'ssn', 'user')

class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=user)
