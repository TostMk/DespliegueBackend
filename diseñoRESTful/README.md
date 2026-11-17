# API RESTful de personajes y habilidades

Este subproyecto conserva la estructura RESTful y los datos de ejemplo de 08.1. Para la entrega basada en 09.1, usa el proyecto principal de la carpeta superior: allí estos datos y la estructura de rutas están conectados a SQLite y Django ORM con los modelos y relaciones requeridos por 09.1.

## Ejecución en Windows

Desde esta carpeta:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py runserver
```

Servidor local: `http://127.0.0.1:8000`.

## Rutas

| Método | Ruta | Uso |
|---|---|---|
| GET | `/api/personajes/` | Listar personajes. Filtros opcionales: `?nombre=elyra` y `?tipo=maga`. |
| POST | `/api/personajes/` | Crear un personaje. |
| GET | `/api/personajes/{id}/` | Consultar un personaje. |
| PUT | `/api/personajes/{id}/` | Reemplazar sus campos; requiere el objeto completo. |
| PATCH | `/api/personajes/{id}/` | Actualizar solo los campos enviados. |
| DELETE | `/api/personajes/{id}/` | Eliminarlo. |
| GET | `/api/habilidades/` | Listar habilidades. Admite `?orden=estamina` o `?orden=nombre`. |
| POST | `/api/habilidades/` | Crear una habilidad. |
| GET | `/api/habilidades/{id}/` | Consultar una habilidad. |
| PUT | `/api/habilidades/{id}/` | Reemplazar sus campos; requiere el objeto completo. |
| PATCH | `/api/habilidades/{id}/` | Actualizar solo los campos enviados. |
| DELETE | `/api/habilidades/{id}/` | Eliminarla y quitar su ID de los personajes asociados. |

Los cuerpos de escritura deben ser JSON. Los datos del proyecto se guardan en listas Python en memoria, como estaban planteados en el ZIP; por eso los cambios hechos mediante la API se reinician cuando se reinicia el servidor.

## Códigos HTTP

- `200`: consulta o actualización correcta.
- `201`: recurso creado.
- `204`: recurso eliminado correctamente; no hay cuerpo de respuesta.
- `400`: JSON inválido, campos faltantes o valores no válidos.
- `404`: el ID solicitado no existe.
- `405`: el método no está habilitado para la ruta.
- `409`: se intenta crear una habilidad con un nombre ya usado.
