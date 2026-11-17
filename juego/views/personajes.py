from .base import HandlerController
from .. import handlers


class PersonajeListView(HandlerController):
    handler = staticmethod(handlers.personajes)


class PersonajeDetailView(HandlerController):
    handler = staticmethod(handlers.personaje_detalle)


class PersonajeHabilidadesView(HandlerController):
    handler = staticmethod(handlers.habilidades_personaje)


class PersonajeHabilidadDetailView(HandlerController):
    handler = staticmethod(handlers.quitar_habilidad)
