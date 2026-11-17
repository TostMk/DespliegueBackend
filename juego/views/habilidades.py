from .base import HandlerController
from .. import handlers


class HabilidadListView(HandlerController):
    handler = staticmethod(handlers.habilidades)


class HabilidadDetailView(HandlerController):
    handler = staticmethod(handlers.habilidad_detalle)
