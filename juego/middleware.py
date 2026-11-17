import json

from .models import RequestLog


class RequestLoggingMiddleware:
    """Registra cada solicitud HTTP antes de ejecutar el controlador."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get("REMOTE_ADDR") or None
        RequestLog.objects.create(
            method=request.method[:10],
            path=request.path[:255],
            ip=ip,
        )
        return self.get_response(request)


class SanitizeIdsMiddleware:
    """Oculta claves id/_id e IDs de habilidades en respuestas JSON."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Los endpoints de identidad usan el id como parte de su contrato de respuesta.
        preserve_ids = request.path in {"/api/me/", "/api/users/"}
        if (not preserve_ids
                and response.get("Content-Type", "").startswith("application/json")
                and not getattr(response, "streaming", False)):
            try:
                data = json.loads(response.content)
                cleaned = self._strip_id_suffixes(data)
                content = json.dumps(cleaned, ensure_ascii=False).encode(response.charset or "utf-8")
                response.content = content
                response.headers["Content-Length"] = str(len(content))
            except (ValueError, TypeError, UnicodeDecodeError):
                pass
        return response

    @classmethod
    def _strip_id_suffixes(cls, data):
        if isinstance(data, dict):
            return {key: cls._strip_id_suffixes(value) for key, value in data.items()
                    if key != "id" and not key.endswith("_id")
                    # Este endpoint expone aquí una lista de IDs numéricos, no datos de habilidades.
                    and key != "habilidades"}
        if isinstance(data, list):
            return [cls._strip_id_suffixes(item) for item in data]
        return data
