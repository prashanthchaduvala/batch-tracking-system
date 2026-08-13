from rest_framework import permissions

class IsAuthenticatedOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
    Custom permission to allow read-only access for authenticated users
    """
    pass

class HasValidToken(permissions.BasePermission):
    """
    Custom permission to check if the token is valid
    """
    def has_permission(self, request, view):
        # JWT validation is handled by the authentication class
        return request.user and request.user.is_authenticated