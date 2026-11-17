from .base import HandlerController
from .. import handlers


class UsuarioPersonajesView(HandlerController):
    handler = staticmethod(handlers.personajes_usuario)
