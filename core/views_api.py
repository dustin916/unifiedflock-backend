from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, permissions

from django.db.models import Q

from .models import Church, ChurchUser, Announcement, Event, PrayerRequest, JoinRequest
from .serializers import (
    ChurchSerializer, AnnouncementSerializer, EventSerializer, PrayerRequestSerializer, JoinRequestSerializer, ChurchUserSerializer
)

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        memberships = user.memberships.all()

        user_churches = []
        for m in memberships:
            user_churches.append({
                'id': m.church.id,
                'name': m.church.name,
                'role': m.role,
            })

        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'churches': user_churches
        })

class ChurchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Provides 'list' and 'retrieve' for Churches.
    """
    serializer_class = ChurchSerializer

    def get_queryset(self):
        return Church.objects.filter(memberships__user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        church=self.get_object()
        user = request.user

        membership = ChurchUser.objects.get(user=user, church=church)
        is_admin = membership.role == 'admin'

        latest_announcement = Announcement.objects.filter(church=church).order_by('-is_pinned', '-created').first()
        events = Event.objects.filter(church=church).order_by('start')[:3]
        prayers = PrayerRequest.objects.filter(church=church).filter(
            Q(approved=True) | Q(created_by=user)
        ).order_by('-created')[:3]

        return Response({
            'name': church.name,
            'is_admin': is_admin,
            'latest_announcement': AnnouncementSerializer(latest_announcement).data if latest_announcement else None,
            'events': EventSerializer(events, many=True).data,
            'prayers': PrayerRequestSerializer(prayers, many=True, context={'request': request}).data,
            'admin_alerts': {
                'pending_joins': JoinRequest.objects.filter(church=church, approved=None).count() if is_admin else 0,
                'pending_prayers': PrayerRequest.objects.filter(church=church, approved=None).count() if is_admin else 0,
            }
        })
    
class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    filterset_fields = ['church']

    def get_queryset(self):
        return Announcement.objects.filter(church__memberships__user=self.request.user)

class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    filterset_fields = ['church']

    def get_queryset(self):
        return Event.objects.filter(church_memberships__user=self.request.user)
    
class PrayerRequestViewSet(viewsets.ModelViewSet):
    serializer_class = PrayerRequestSerializer
    filterset_fields = ['church', 'approved']

    def get_queryset(self):
        user = self.request.user
        return Event.objects.filter(
            church_memberships__user=user
            ).filter(
                Q(approved=True) | Q(created_by=self.request.user)
            )
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)