from django.urls import path

from . import views

urlpatterns = [
    path('personajes/', views.personajes_list, name='personajes-list'),
    path('personajes/<int:id>/', views.personaje_detail, name='personaje-detail'),
    path('habilidades/', views.habilidades_list, name='habilidades-list'),
    path('habilidades/<int:id>/', views.habilidad_detail, name='habilidad-detail'),
]
