from rest_framework.permissions import BasePermission


class IsDuelParticipant(BasePermission):
    """Allow access only to duel creator or opponent."""

    def has_object_permission(self, request, view, obj):
        return request.user in [obj.creator, obj.opponent]


class IsBugCreator(BasePermission):
    """Allow access only to the bug creator."""

    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user


class IsOwnerOrReadOnly(BasePermission):
    """Allow read for anyone, write only for the owner."""

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if hasattr(obj, 'creator'):
            return obj.creator == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        if hasattr(obj, 'sender'):
            return obj.sender == request.user
        return False


class IsAdminOrReadOnly(BasePermission):
    """Allow read for anyone, write only for admins."""

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user and request.user.is_staff
