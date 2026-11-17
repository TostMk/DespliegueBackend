import json

from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .forms import HabilidadForm, PersonajeForm, PersonajeHabilidadForm
from .models import Habilidad, Personaje, PersonajeHabilidad, Perfil, Usuario


def error(mensaje, status=400):
    return JsonResponse({"error": mensaje}, status=status)


def leer_json(request):
    try:
        data = json.loads(request.body or b"")
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("El cuerpo debe contener JSON válido.")
    if not isinstance(data, dict):
        raise ValueError("El cuerpo JSON debe ser un objeto.")
    return data


def metodo_no_permitido(metodos):
    response = error("Método no permitido.", 405)
    response["Allow"] = ", ".join(metodos)
    return response


def datos_habilidad(habilidad, nivel=None):
    data = {
        "id": habilidad.id,
        "nombre": habilidad.nombre,
        "descripcion": habilidad.descripcion,
        "incremento_ataque": habilidad.incremento_ataque,
        "incremento_defensa": habilidad.incremento_defensa,
        "incremento_estamina": habilidad.incremento_estamina,
    }
    if nivel is not None:
        data["nivel"] = nivel
    return data


def datos_personaje(personaje, detalle=False, orden=None):
    relaciones = PersonajeHabilidad.objects.filter(personaje=personaje).select_related("habilidad")
    if orden:
        orden = orden.casefold()
        campos_habilidad = {
            "ataque": "incremento_ataque",
            "defensa": "incremento_defensa",
            "estamina": "incremento_estamina",
            "nombre": "nombre",
        }
        if orden == "id":
            relaciones = relaciones.order_by("habilidad_id")
        elif orden in campos_habilidad:
            relaciones = relaciones.order_by("-habilidad__" + campos_habilidad[orden], "habilidad_id")
    relaciones = list(relaciones)
    ataque, defensa, estamina = personaje.ataque, personaje.defensa, personaje.estamina
    for relacion in relaciones:
        habilidad, nivel = relacion.habilidad, relacion.nivel
        ataque += habilidad.incremento_ataque * nivel
        defensa += habilidad.incremento_defensa * nivel
        estamina += habilidad.incremento_estamina * nivel
    data = {
        "id": personaje.id,
        "nombre": personaje.nombre,
        "tipo": personaje.tipo,
        "descripcion": personaje.descripcion,
        "ataque": personaje.ataque,
        "defensa": personaje.defensa,
        "estamina": personaje.estamina,
        "habilidades": [r.habilidad_id for r in relaciones],
        "atributos_efectivos": {"ataque": ataque, "defensa": defensa, "estamina": estamina},
    }
    if detalle:
        data["habilidades_detalle"] = [datos_habilidad(r.habilidad, r.nivel) for r in relaciones]
    return data


def validar_texto(data, campo, requerido=False):
    value = data.get(campo)
    if value is None and not requerido:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{campo} debe ser un texto no vacío.")
    return value.strip()


def validar_entero(data, campo, requerido=False, permitir_negativo=False):
    value = data.get(campo)
    if value is None and not requerido:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{campo} debe ser un entero.")
    if not permitir_negativo and value < 0:
        raise ValueError(f"{campo} debe ser mayor o igual a cero.")
    return value


PERSONAJE_CAMPOS = ("nombre", "tipo", "descripcion", "ataque", "defensa", "estamina")
HABILIDAD_CAMPOS = (
    "nombre", "descripcion", "incremento_ataque", "incremento_defensa", "incremento_estamina"
)


def ordenar_personajes(queryset, orden):
    campos = {
        "ataque": "ataque",
        "defensa": "defensa",
        "estamina": "estamina",
        "nombre": "nombre",
    }
    if not orden:
        return queryset
    orden = orden.casefold()
    if orden == "id":
        return queryset.order_by("id")
    if orden not in campos:
        raise ValueError("El parámetro orden admite id, ataque, defensa, estamina o nombre.")
    return queryset.order_by("-" + campos[orden], "id")


def ordenar_habilidades(queryset, orden):
    campos = {
        "ataque": "incremento_ataque",
        "defensa": "incremento_defensa",
        "estamina": "incremento_estamina",
        "nombre": "nombre",
    }
    if not orden:
        return queryset
    orden = orden.casefold()
    if orden == "id":
        return queryset.order_by("id")
    if orden not in campos:
        raise ValueError("El parámetro orden admite id, ataque, defensa, estamina o nombre.")
    return queryset.order_by("-" + campos[orden], "id")


@csrf_exempt
def personajes(request):
    if request.method == "GET":
        queryset = Personaje.objects.all()
        nombre = request.GET.get("nombre", "").strip()
        tipo = request.GET.get("tipo", "").strip()
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        if tipo:
            queryset = queryset.filter(tipo__iexact=tipo)
        try:
            queryset = ordenar_personajes(queryset, request.GET.get("orden"))
        except ValueError as exc:
            return error(str(exc))
        return JsonResponse([datos_personaje(p) for p in queryset], safe=False)

    if request.method != "POST":
        return metodo_no_permitido(["GET", "POST"])
    try:
        data = leer_json(request)
        unknown = set(data) - set(PERSONAJE_CAMPOS) - {"perfil_id", "habilidades"}
        if unknown:
            return error("Campos no permitidos: " + ", ".join(sorted(unknown)))
        required = {"nombre", "descripcion", "ataque", "defensa", "estamina", "perfil_id"}
        if required - set(data):
            return error("Faltan campos obligatorios: " + ", ".join(sorted(required - set(data))))
        form = PersonajeForm(data)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
        perfil_id = form.cleaned_data.get("perfil_id")
        if not perfil_id:
            return error("perfil_id es obligatorio.")
        perfil = Perfil.objects.get(pk=perfil_id)
        ids_habilidades = form.cleaned_data["habilidades"]
        habilidades = list(Habilidad.objects.filter(pk__in=ids_habilidades))
        if len(habilidades) != len(ids_habilidades):
            return error("Una o más habilidades no existen.", 404)
        with transaction.atomic():
            personaje = form.save(commit=False)
            personaje.perfil = perfil
            personaje.save()
            PersonajeHabilidad.objects.bulk_create([
                PersonajeHabilidad(personaje=personaje, habilidad=h, nivel=1) for h in habilidades
            ])
        return JsonResponse(datos_personaje(personaje, detalle=True), status=201)
    except ValueError as exc:
        return error(str(exc))
    except Perfil.DoesNotExist:
        return error("No existe el perfil indicado en perfil_id.", 404)


def personajes_usuario(request, usuario_id):
    if request.method != "GET":
        return metodo_no_permitido(["GET"])
    if not Usuario.objects.filter(pk=usuario_id).exists():
        return error("No existe ese usuario.", 404)
    queryset = Personaje.objects.filter(perfil__usuario_id=usuario_id)
    try:
        queryset = ordenar_personajes(queryset, request.GET.get("orden"))
    except ValueError as exc:
        return error(str(exc))
    return JsonResponse([datos_personaje(p) for p in queryset], safe=False)


@csrf_exempt
def personaje_detalle(request, personaje_id):
    try:
        personaje = Personaje.objects.get(pk=personaje_id)
    except Personaje.DoesNotExist:
        return error("No existe ese personaje.", 404)
    if request.method == "GET":
        orden = request.GET.get("orden")
        if orden and orden.casefold() not in ("id", "ataque", "defensa", "estamina", "nombre"):
            return error("El parámetro orden admite id, ataque, defensa, estamina o nombre.")
        return JsonResponse(datos_personaje(personaje, detalle=True, orden=orden))
    if request.method == "DELETE":
        personaje.delete()
        return HttpResponse(status=204)
    if request.method not in ("PUT", "PATCH"):
        return metodo_no_permitido(["GET", "PUT", "PATCH", "DELETE"])
    try:
        data = leer_json(request)
        desconocidos = set(data) - set(PERSONAJE_CAMPOS)
        if desconocidos:
            raise ValueError("Campos no permitidos: " + ", ".join(sorted(desconocidos)))
        if request.method == "PUT":
            # 09.1 define estos atributos; tipo se conserva como extensión de 08.1.
            faltantes = set(PERSONAJE_CAMPOS) - {"tipo"} - set(data)
            if faltantes:
                raise ValueError("PUT requiere todos los campos: " + ", ".join(sorted(faltantes)))
        if request.method == "PUT":
            required = {"nombre", "descripcion", "ataque", "defensa", "estamina"}
            if required - set(data):
                return error("PUT requiere todos los campos: " + ", ".join(sorted(required - set(data))))
        if "perfil_id" in data or "habilidades" in data:
            return error("No se puede cambiar perfil ni habilidades desde este endpoint.")
        if request.method == "PATCH":
            actuales = {field: getattr(personaje, field) for field in PERSONAJE_CAMPOS}
            actuales.update(data)
            data = actuales
        form = PersonajeForm(data, instance=personaje)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
        personaje = form.save()
        return JsonResponse(datos_personaje(personaje, detalle=True))
    except ValueError as exc:
        return error(str(exc))
    except Exception as exc:
        from django.core.exceptions import ValidationError
        if isinstance(exc, ValidationError):
            return error("Revisa los campos: " + "; ".join(exc.messages))
        raise


@csrf_exempt
def habilidades_personaje(request, personaje_id):
    try:
        personaje = Personaje.objects.get(pk=personaje_id)
    except Personaje.DoesNotExist:
        return error("No existe ese personaje.", 404)
    if request.method == "GET":
        try:
            orden = request.GET.get("orden", "").casefold()
            campos = {
                "ataque": "incremento_ataque",
                "defensa": "incremento_defensa",
                "estamina": "incremento_estamina",
                "nombre": "nombre",
            }
            queryset = PersonajeHabilidad.objects.filter(personaje=personaje).select_related("habilidad")
            if orden == "id":
                queryset = queryset.order_by("habilidad_id")
            elif orden in campos:
                queryset = queryset.order_by("-habilidad__" + campos[orden], "habilidad_id")
            elif orden:
                raise ValueError("El parámetro orden admite id, ataque, defensa, estamina o nombre.")
        except ValueError as exc:
            return error(str(exc))
        return JsonResponse([datos_habilidad(r.habilidad, r.nivel) for r in queryset], safe=False)
    if request.method != "POST":
        return metodo_no_permitido(["GET", "POST"])
    try:
        data = leer_json(request)
        unknown = set(data) - {"habilidad_id", "nivel"}
        if unknown:
            return error("Campos no permitidos: " + ", ".join(sorted(unknown)))
        form = PersonajeHabilidadForm(data)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
        habilidad = Habilidad.objects.get(pk=form.cleaned_data["habilidad_id"])
        nivel = form.cleaned_data["nivel"]
        relacion, creada = PersonajeHabilidad.objects.update_or_create(
            personaje=personaje, habilidad=habilidad, defaults={"nivel": nivel}
        )
        return JsonResponse({
            "mensaje": "Habilidad agregada correctamente." if creada else "Nivel de habilidad actualizado.",
            "habilidad": datos_habilidad(habilidad, relacion.nivel),
            "atributos_efectivos": datos_personaje(personaje)["atributos_efectivos"],
        }, status=201 if creada else 200)
    except ValueError as exc:
        return error(str(exc))
    except Habilidad.DoesNotExist:
        return error("No existe la habilidad indicada en habilidad_id.", 404)


@csrf_exempt
def quitar_habilidad(request, personaje_id, habilidad_id):
    if request.method != "DELETE":
        return metodo_no_permitido(["DELETE"])
    try:
        relacion = PersonajeHabilidad.objects.select_related("personaje").get(
            personaje_id=personaje_id, habilidad_id=habilidad_id
        )
    except PersonajeHabilidad.DoesNotExist:
        return error("El personaje no tiene esa habilidad.", 404)
    personaje = relacion.personaje
    relacion.delete()
    return JsonResponse({
        "mensaje": "Habilidad retirada correctamente.",
        "atributos_efectivos": datos_personaje(personaje)["atributos_efectivos"],
    })


@csrf_exempt
def habilidades(request):
    if request.method == "GET":
        queryset = Habilidad.objects.all()
        try:
            queryset = ordenar_habilidades(queryset, request.GET.get("orden"))
        except ValueError as exc:
            return error(str(exc))
        return JsonResponse([datos_habilidad(h) for h in queryset], safe=False)
    if request.method != "POST":
        return metodo_no_permitido(["GET", "POST"])
    try:
        data = leer_json(request)
        unknown = set(data) - set(HABILIDAD_CAMPOS)
        if unknown:
            return error("Campos no permitidos: " + ", ".join(sorted(unknown)))
        form = HabilidadForm(data)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
        habilidad = form.save()
        return JsonResponse(datos_habilidad(habilidad), status=201)
    except ValueError as exc:
        return error(str(exc))
    except IntegrityError:
        return error("Ya existe una habilidad con ese nombre.", 409)


def validar_datos_habilidad(data, completo):
    desconocidos = set(data) - set(HABILIDAD_CAMPOS)
    if desconocidos:
        raise ValueError("Campos no permitidos: " + ", ".join(sorted(desconocidos)))
    if completo:
        faltantes = set(HABILIDAD_CAMPOS) - set(data)
        if faltantes:
            raise ValueError("Faltan campos obligatorios: " + ", ".join(sorted(faltantes)))
    payload = {}
    for campo in ("nombre", "descripcion"):
        if campo in data:
            payload[campo] = validar_texto(data, campo, requerido=True)
    for campo in ("incremento_ataque", "incremento_defensa", "incremento_estamina"):
        if campo in data:
            payload[campo] = validar_entero(data, campo, requerido=True, permitir_negativo=True)
    return payload


@csrf_exempt
def habilidad_detalle(request, habilidad_id):
    try:
        habilidad = Habilidad.objects.get(pk=habilidad_id)
    except Habilidad.DoesNotExist:
        return error("No existe esa habilidad.", 404)
    if request.method == "GET":
        return JsonResponse(datos_habilidad(habilidad))
    if request.method == "DELETE":
        habilidad.delete()
        return HttpResponse(status=204)
    if request.method not in ("PUT", "PATCH"):
        return metodo_no_permitido(["GET", "PUT", "PATCH", "DELETE"])
    try:
        data = leer_json(request)
        unknown = set(data) - set(HABILIDAD_CAMPOS)
        if unknown:
            return error("Campos no permitidos: " + ", ".join(sorted(unknown)))
        if request.method == "PATCH":
            actuales = {field: getattr(habilidad, field) for field in HABILIDAD_CAMPOS}
            actuales.update(data)
            data = actuales
        form = HabilidadForm(data, instance=habilidad)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
        habilidad = form.save()
        return JsonResponse(datos_habilidad(habilidad))
    except ValueError as exc:
        return error(str(exc))
    except IntegrityError:
        return error("Ya existe una habilidad con ese nombre.", 409)
    except Exception as exc:
        from django.core.exceptions import ValidationError
        if isinstance(exc, ValidationError):
            return error("Revisa los campos: " + "; ".join(exc.messages))
        raise
