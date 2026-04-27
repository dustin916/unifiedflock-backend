from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Church, Member, ChurchUser, Announcement, Event, PrayerRequest, JoinRequest, Notification, ChatMessage

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class ChurchSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    class Meta:
        model = Church
        fields = ['id', 'name', 'role']

    def get_role(self, obj):
        request = self.context.get('request')
        if request and request.user:
            membership = ChurchUser.objects.filter(church=obj, user=request.user).first()
            return membership.role if membership else None
        return None

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = '__all__'

class ChurchUserSerializer(serializers.ModelSerializer):
    church_name = serializers.ReadOnlyField(source='church.name')
    user_name = serializers.ReadOnlyField(source='user.username')
    first_name = serializers.ReadOnlyField(source='user.first_name')
    last_name = serializers.ReadOnlyField(source='user.last_name')

    class Meta:
        model = ChurchUser
        fields = ['id', 'user', 'first_name', 'last_name', 'user_name', 'church', 'church_name', 'role', 'joined']

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'
        read_only_fields = ['created_by']

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'
        
class PrayerRequestSerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = PrayerRequest
        fields = '__all__'
    
    def get_user_full_name(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        return f"{obj.created_by.first_name} {obj.created_by.last_name}" if obj.created_by else "Unknown"
        
    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request:
            return obj.created_by == request.user
        return False
        
class JoinRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = JoinRequest
        fields = '__all__'
        
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        
class ChatMessageSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = ChatMessage
        fields = ['id', 'church', 'user', 'user_name', 'message', 'created']
