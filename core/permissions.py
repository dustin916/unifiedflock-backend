from rest_framework import permissions
from .models import ChurchUser

class IsChurchAdminOrReadOnly(permissions.BasePermission):
    """
    Allows safe methods (GET) for anyone, but restricts
    POST, PUT, DELETE to church admins.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user.is_authenticated:
            return False

        if request.method == 'POST':
            church_id = request.data.get('church')
            if not church_id:
                return False
            return ChurchUser.objects.filter(
                user=request.user,
                church_id=church_id,
                role='admin'
            ).exists()

        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return ChurchUser.objects.filter(
            user=request.user,
            church=obj.church,
            role='admin'
        ).exists()

class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    For Prayer Requests: Anyone can view, anyone can create.
    Only the creator or an admin can edit/delete.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        is_admin = ChurchUser.objects.filter(
            user=request.user,
            church=obj.church,
            role='admin'
        ).exists()

        return obj.created_by == request.user or is_admin