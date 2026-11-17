from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..permissions import IsAdmin


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    profile = getattr(user, "profile", None)
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": profile.role if profile else None,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdmin])
def list_users(request):
    users = User.objects.order_by("id").values("id", "username", "email")
    return Response(list(users))
