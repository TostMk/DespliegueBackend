import json

from django.contrib import admin
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from django.views.decorators.http import require_GET
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from juego.views.habilidades import HabilidadDetailView, HabilidadListView
from juego.views.personajes import (
    PersonajeDetailView,
    PersonajeHabilidadDetailView,
    PersonajeHabilidadesView,
    PersonajeListView,
)
from juego.views.usuarios import UsuarioPersonajesView
from juego.views.auth import list_users, me


@require_GET
def authors(request):
    """Endpoint público de verificación del equipo, configurado con AUTHORS (JSON)."""
    try:
        team = json.loads(settings.AUTHORS_JSON)
    except (TypeError, json.JSONDecodeError):
        return JsonResponse(
            {"error": "La variable AUTHORS debe ser una lista JSON válida."}, status=500
        )
    if not isinstance(team, list) or any(
        not isinstance(member, dict)
        or not isinstance(member.get("nombre"), str)
        or not isinstance(member.get("codigo"), str)
        for member in team
    ):
        return JsonResponse(
            {"error": "AUTHORS debe contener objetos con nombre y codigo."}, status=500
        )
    return JsonResponse(team, safe=False)


urlpatterns = [
    path("authors", authors, name="authors"),
    path("admin/", admin.site.urls),
    path("api/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/me/", me, name="me"),
    path("api/users/", list_users, name="users"),
    path("api/personajes", PersonajeListView.as_view(), name="personajes"),
    path("api/personajes/", PersonajeListView.as_view()),
    path("api/personajes/<int:personaje_id>", PersonajeDetailView.as_view(), name="personaje-detalle"),
    path("api/personajes/<int:personaje_id>/", PersonajeDetailView.as_view()),
    path("api/usuarios/<int:usuario_id>/personajes", UsuarioPersonajesView.as_view(), name="personajes-usuario"),
    path("api/usuarios/<int:usuario_id>/personajes/", UsuarioPersonajesView.as_view()),
    path("api/personajes/<int:personaje_id>/habilidades", PersonajeHabilidadesView.as_view(), name="habilidades-personaje"),
    path("api/personajes/<int:personaje_id>/habilidades/", PersonajeHabilidadesView.as_view()),
    path("api/personajes/<int:personaje_id>/habilidades/<int:habilidad_id>", PersonajeHabilidadDetailView.as_view(), name="quitar-habilidad"),
    path("api/personajes/<int:personaje_id>/habilidades/<int:habilidad_id>/", PersonajeHabilidadDetailView.as_view()),
    path("api/habilidades", HabilidadListView.as_view(), name="habilidades"),
    path("api/habilidades/", HabilidadListView.as_view()),
    path("api/habilidades/<int:habilidad_id>", HabilidadDetailView.as_view(), name="habilidad-detalle"),
    path("api/habilidades/<int:habilidad_id>/", HabilidadDetailView.as_view()),
]
