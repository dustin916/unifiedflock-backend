from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.shortcuts import get_object_or_404

from .models import Church, ChurchUser, Announcement, Event, PrayerRequest, JoinRequest

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

@api_view(['GET'])
def church_dashboard_api(request, church_id):
    church = get_object_or_404(Church, id=church_id)
    membership = ChurchUser.objects.filter(user=request.user, church=church).first()

    if not membership:
        return Response({'error': 'Not a member'}, status=403)
    
    is_admin = membership.role == 'admin'

    latest_announcement = Announcement.objects.filter(church=church).order_by('-is_pinned', '-created').first()
    events = Event.objects.filter(church=church).order_by('start')[:3]
    prayers = PrayerRequest.objects.filter(church=church, approved=True).order_by('-created')[:3]

    pending_join_count = JoinRequest.objects.filter(church=church, approved=None).count() if is_admin else 0
    pending_prayer_count = PrayerRequest.objects.filter(church=church, approved=None).count() if is_admin else 0

    return Response({
        'name': church.name,
        'is_admin': is_admin,
        'latest_announcement': {
            'title': latest_announcement.title,
            'message': latest_announcement.message
        } if latest_announcement else None,
        'events': [
            {
                'id': e.id, 
                'name': e.name, 
                'start': e.start, 
                'description': e.description
            } for e in events
        ],
        'prayers': [
            {
                'id': p.id, 
                'request': p.request, 
                'is_anonymous': p.is_anonymous, 
                'user_name': f"{p.created_by.first_name} {p.created_by.last_name}" if not p.is_anonymous else "Anonymous"
            } for p in prayers
        ],
        'admin_alerts': {
            'pending_joins': pending_join_count,
            'pending_prayers': pending_prayer_count,
        }
    })