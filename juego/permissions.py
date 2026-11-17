from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    message = "Acceso prohibido. Se requiere rol ADMIN."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated
            and hasattr(user, "profile")
            and user.profile.role == "ADMIN"
        )
