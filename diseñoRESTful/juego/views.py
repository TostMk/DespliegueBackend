import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .datos import HABILIDADES, PERSONAJES

PERSONAJE_FIELDS = {
    'nombre', 'tipo', 'descripcion', 'ataque', 'defensa', 'estamina', 'habilidades'
}
HABILIDAD_FIELDS = {
    'nombre', 'descripcion', 'incremento_ataque', 'incremento_defensa',
    'incremento_estamina'
}
INCREMENT_FIELDS = {
    'incremento_ataque', 'incremento_defensa', 'incremento_estamina'
}


def _respuesta_error(mensaje, status=400):
    return JsonResponse({'error': mensaje}, status=status)


def _leer_json(request):
    try:
        datos = json.loads(request.body or b'')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return datos if isinstance(datos, dict) else None


def _validar_personaje(datos, actual=None, reemplazo=False):
    if datos is None:
        return None, 'El cuerpo debe ser un objeto JSON válido.'
    desconocidos = set(datos) - PERSONAJE_FIELDS
    if desconocidos:
        return None, f'Campos no permitidos: {", ".join(sorted(desconocidos))}.'
    valores = dict(actual or {})
    if reemplazo:
        faltantes = PERSONAJE_FIELDS - set(datos)
        if faltantes:
            return None, f'Faltan campos obligatorios: {", ".join(sorted(faltantes))}.'
        valores = {}
    valores.update(datos)
    requeridos = PERSONAJE_FIELDS if actual is None else set(datos)
    faltantes = requeridos - set(valores)
    if faltantes:
        return None, f'Faltan campos obligatorios: {", ".join(sorted(faltantes))}.'
    for campo in ('nombre', 'tipo', 'descripcion'):
        if campo in valores and (not isinstance(valores[campo], str) or not valores[campo].strip()):
            return None, f'{campo} debe ser un texto no vacío.'
    for campo in ('ataque', 'defensa', 'estamina'):
        if campo in valores and (not isinstance(valores[campo], int) or isinstance(valores[campo], bool) or valores[campo] < 0):
            return None, f'{campo} debe ser un entero mayor o igual a cero.'
    if 'habilidades' in valores:
        habilidades = valores['habilidades']
        ids_validos = {h['id'] for h in HABILIDADES}
        if not isinstance(habilidades, list) or any(not isinstance(i, int) or isinstance(i, bool) for i in habilidades):
            return None, 'habilidades debe ser una lista de identificadores enteros.'
        if len(habilidades) != len(set(habilidades)):
            return None, 'No se permiten identificadores de habilidad repetidos.'
        inexistentes = set(habilidades) - ids_validos
        if inexistentes:
            return None, f'No existen las habilidades: {", ".join(map(str, sorted(inexistentes)))}.'
    return valores, None


def _validar_habilidad(datos, actual=None, reemplazo=False):
    if datos is None:
        return None, 'El cuerpo debe ser un objeto JSON válido.'
    desconocidos = set(datos) - HABILIDAD_FIELDS
    if desconocidos:
        return None, f'Campos no permitidos: {", ".join(sorted(desconocidos))}.'
    valores = dict(actual or {})
    if reemplazo:
        faltantes = HABILIDAD_FIELDS - set(datos)
        if faltantes:
            return None, f'Faltan campos obligatorios: {", ".join(sorted(faltantes))}.'
        valores = {}
    valores.update(datos)
    requeridos = HABILIDAD_FIELDS if actual is None else set(datos)
    faltantes = requeridos - set(valores)
    if faltantes:
        return None, f'Faltan campos obligatorios: {", ".join(sorted(faltantes))}.'
    for campo in ('nombre', 'descripcion'):
        if campo in valores and (not isinstance(valores[campo], str) or not valores[campo].strip()):
            return None, f'{campo} debe ser un texto no vacío.'
    for campo in INCREMENT_FIELDS:
        if campo in valores and (not isinstance(valores[campo], int) or isinstance(valores[campo], bool)):
            return None, f'{campo} debe ser un entero.'
    return valores, None


def _buscar(registros, id):
    return next((registro for registro in registros if registro['id'] == id), None)


def _siguiente_id(registros):
    return max((registro['id'] for registro in registros), default=0) + 1


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def personajes_list(request):
    if request.method == 'GET':
        resultado = PERSONAJES
        nombre = request.GET.get('nombre', '').strip().casefold()
        tipo = request.GET.get('tipo', '').strip().casefold()
        if nombre:
            resultado = [p for p in resultado if nombre in p['nombre'].casefold()]
        if tipo:
            resultado = [p for p in resultado if p['tipo'].casefold() == tipo]
        return JsonResponse(resultado, safe=False, status=200)

    valores, error = _validar_personaje(_leer_json(request))
    if error:
        return _respuesta_error(error)
    personaje = {'id': _siguiente_id(PERSONAJES), **valores}
    PERSONAJES.append(personaje)
    return JsonResponse(personaje, status=201)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def personaje_detail(request, id):
    personaje = _buscar(PERSONAJES, id)
    if personaje is None:
        return _respuesta_error('Personaje no encontrado.', 404)
    if request.method == 'GET':
        return JsonResponse(personaje, status=200)
    if request.method == 'DELETE':
        PERSONAJES.remove(personaje)
        return HttpResponse(status=204)

    valores, error = _validar_personaje(
        _leer_json(request), actual=personaje,
        reemplazo=request.method == 'PUT'
    )
    if error:
        return _respuesta_error(error)
    personaje.update(valores)
    return JsonResponse(personaje, status=200)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def habilidades_list(request):
    if request.method == 'GET':
        resultado = HABILIDADES
        orden = request.GET.get('orden', '').casefold()
        if orden == 'estamina':
            resultado = sorted(resultado, key=lambda h: h['incremento_estamina'], reverse=True)
        elif orden and orden != 'nombre':
            return _respuesta_error('El parámetro orden admite nombre o estamina.')
        elif orden == 'nombre':
            resultado = sorted(resultado, key=lambda h: h['nombre'].casefold())
        return JsonResponse(resultado, safe=False, status=200)

    valores, error = _validar_habilidad(_leer_json(request))
    if error:
        return _respuesta_error(error)
    if any(h['nombre'].casefold() == valores['nombre'].casefold() for h in HABILIDADES):
        return _respuesta_error('Ya existe una habilidad con ese nombre.', 409)
    habilidad = {'id': _siguiente_id(HABILIDADES), **valores}
    HABILIDADES.append(habilidad)
    return JsonResponse(habilidad, status=201)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def habilidad_detail(request, id):
    habilidad = _buscar(HABILIDADES, id)
    if habilidad is None:
        return _respuesta_error('Habilidad no encontrada.', 404)
    if request.method == 'GET':
        return JsonResponse(habilidad, status=200)
    if request.method == 'DELETE':
        HABILIDADES.remove(habilidad)
        for personaje in PERSONAJES:
            personaje['habilidades'] = [hid for hid in personaje['habilidades'] if hid != id]
        return HttpResponse(status=204)

    valores, error = _validar_habilidad(
        _leer_json(request), actual=habilidad,
        reemplazo=request.method == 'PUT'
    )
    if error:
        return _respuesta_error(error)
    if any(h['id'] != id and h['nombre'].casefold() == valores['nombre'].casefold() for h in HABILIDADES):
        return _respuesta_error('Ya existe una habilidad con ese nombre.', 409)
    habilidad.update(valores)
    return JsonResponse(habilidad, status=200)
