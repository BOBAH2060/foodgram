from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Allow read-only access for all and write access only for the author."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
