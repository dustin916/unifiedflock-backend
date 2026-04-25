from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, permissions, status

from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Church, ChurchUser, Announcement, Event, PrayerRequest, JoinRequest, Notification
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
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['church']

    def get_queryset(self):
        return Announcement.objects.filter(church__memberships__user=self.request.user)

class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['church']

    def get_queryset(self):
        return Event.objects.filter(church__memberships__user=self.request.user)
    
class PrayerRequestViewSet(viewsets.ModelViewSet):
    serializer_class = PrayerRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['church', 'approved']

    def get_queryset(self):
        user = self.request.user
        return PrayerRequest.objects.filter(
            church__memberships__user=user
            ).filter(
                Q(approved=True) | Q(created_by=user)
            )
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ChurchUserViewSet(viewsets.ModelViewSet):
    serializer_class = ChurchUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['church']

    def get_queryset(self):
        return ChurchUser.objects.filter(church__memberships__user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def promote(self, request, pk=None):
        membership = self .get_object()

        if not ChurchUser.objects.filter(church=membership.church, user=request.user, role='admin').exists():
            return Response({'error': 'Not Authorized'}, status=403)
        membership.role = 'admin'
        membership.save()
        
        Notification.objects.create( user=membership.user, message=f"You have been promoted to Admin in {membership.church.name}.")

        return Response({'status': 'promoted'})
    
    @action(detail=True, methods=['post'])
    def demote(self, request, pk=None):
        membership = self.get_object()
        if not ChurchUser.objects.filter(church=membership.church, user=request.user, role='admin').exists():
            return Response({'error': 'Not Authorized'}, status=403)
        membership.role = 'member'
        membership.save()

        Notification.objects.create( user=membership.user, message=f"Your role in {membership.church.name} has been changed to Member.")

        return Response({'status': 'demoted'})

    @action(detail=True, methods=['post'])
    def remove(self, request, pk=None):
        membership = self.get_object()
    
        if not ChurchUser.objects.filter(church=membership.church, user=request.user, role='admin').exists():
            return Response({'error': 'Not Authorized'}, status=403)
    
        church_name = membership.church.name
        user_to_notify = membership.user
        
        membership.delete()
    
        Notification.objects.create(user=user_to_notify,message=f"You have been removed from {church_name}.")

        return Response({'status': 'removed'})
    
    @action(detail=False, methods=['post'])
    def quit(self, request):
        church_id = request.data.get('church_id')
        membership = get_object_or_404(ChurchUser, user=request.user, church_id=church_id)
        
        if membership.role == 'admin':
            admin_count = ChurchUser.objects.filter(church_id=church_id, role='admin').count()
            if admin_count <=1: 
                return Response({'error': 'You are the only admin. You cannot leave without assigning another admin first'}, status=400)

        church_name = membership.church.name
        membership.delete()
        
        admins = ChurchUser.objects.filter(church_id=church_id, role='admin')
        for admin in admins:
            Notification.objects.create(user=admin.user, message=f"{request.user.first_name} {request.user.last_name} has left {church_name}.")

        return Response({'status': 'left church'})
    