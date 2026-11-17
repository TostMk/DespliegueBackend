from rest_framework.views import APIView


class HandlerController(APIView):
    handler = None

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def handle(self, request, *args, **kwargs):
        return self.handler(request, *args, **kwargs)

    get = handle
    post = handle
    put = handle
    patch = handle
    delete = handle
