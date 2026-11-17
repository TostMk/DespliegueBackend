# API de juego de rol: despliegue en Render

API Django REST con JWT, perfiles USER/ADMIN, personajes y habilidades. En local usa SQLite; si existe `DATABASE_URL`, usa PostgreSQL. `GET /authors` es público y entrega el equipo configurado en `AUTHORS`.

## Ejecutar localmente (Windows PowerShell)

Desde la raíz del proyecto:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
```

Edita `.env` para cambiar el secreto y los integrantes. Si PowerShell impide activar el entorno:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Instala, migra y ejecuta:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abre `http://127.0.0.1:8000/authors`, `http://127.0.0.1:8000/admin/` o `http://127.0.0.1:8000/static/juego/index.html`. La fixture opcional: `python manage.py loaddata juego/fixtures/datos_iniciales.json`.

## Integrantes del equipo

En `.env`, `AUTHORS` debe ser JSON en una sola línea con los nombres y códigos reales:

```dotenv
AUTHORS=[{"nombre":"Nombre Apellido","codigo":"0000001"},{"nombre":"Otro Integrante","codigo":"0000002"}]
```

Copia el valor a la variable `AUTHORS` de Render también. El valor de ejemplo en `render.yaml` debe reemplazarse antes del deploy; no inventé esos datos.

## Despliegue Render

1. Crea un repositorio GitHub público y sube este proyecto. No subas `.env`, `db.sqlite3` ni `.venv`.
2. En Render crea un **Blueprint** conectado al repositorio: detectará `render.yaml` y propondrá el servicio y PostgreSQL.
3. Reemplaza `AUTHORS` con los integrantes reales. Render genera `SECRET_KEY` y conecta `DATABASE_URL`.
4. Espera el build y verifica `https://<servicio>.onrender.com/authors`.

Build y arranque configurados:

```sh
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --no-input
gunicorn rol_api.wsgi:application --bind 0.0.0.0:$PORT
```

Variables para configuración manual: `SECRET_KEY` aleatoria y privada, `DEBUG=False`, `ALLOWED_HOSTS=.onrender.com`, `DATABASE_URL` (URL interna de PostgreSQL), `AUTHORS` (JSON). Si falta `DATABASE_URL`, Django usa SQLite local. `DEBUG` por defecto es falso.

## Conceptos del taller

- **Desplegar**: publicar el código en un servidor accesible por URL, instalar dependencias, configurar secretos y servicios, migrar la base y arrancar un servidor de producción.
- **Desarrollo y producción**: local usa `runserver`, SQLite y normalmente debug; producción usa Gunicorn, PostgreSQL, secretos externos y `DEBUG=False`.
- **PaaS**: Render administra infraestructura y facilita deploy desde Git, HTTPS y bases de datos. Alternativas del Word: PythonAnywhere, Vercel, Railway, Fly.io, Heroku. Confirma sus planes actuales antes de escoger, sus límites cambian.
- **Variables de entorno**: configuración externa al código para separar valores por entorno y evitar filtrar claves. `.env` es local e ignorado por Git; en Render se declaran en el panel/Blueprint.
- **ORM**: Django convierte operaciones sobre modelos y QuerySets a SQL del motor activo. Por eso cambiamos driver y URL de SQLite a PostgreSQL, sin rehacer modelos ni migraciones.
- **Gunicorn** es servidor WSGI de producción; `runserver` es para desarrollo.
- **PostgreSQL** usa `DATABASE_URL`, que `dj-database-url` interpreta. Los modelos permanecen iguales.
- **`ALLOWED_HOSTS`** restringe dominios aceptados por Django; `.onrender.com` habilita el subdominio.
- **`DEBUG=False`** evita filtrar trazas. **WhiteNoise** sirve estáticos recolectados; su middleware va después de `SecurityMiddleware`. `STATIC_ROOT` es destino de `collectstatic`; `STORAGES` comprime y versiona los archivos.
- **`render.yaml`** declara servicios, base, variables y comandos como infraestructura reproducible.
- **HTTPS**: Render termina TLS en su proxy y enruta el tráfico seguro al servicio.
- **Cold start**: un servicio gratuito puede suspenderse por inactividad; la primera solicitud despierta el servicio y tarda más. Haz una petición antes de una demo.
- La guía advierte que PostgreSQL gratuito tiene plazo; respalda los datos y verifica la política vigente antes de depender de un plan gratuito. Supabase y Neon son alternativas citadas para PostgreSQL, con límites.
- Seguridad: no subir secretos; HTTPS; `DEBUG=False`; restringir hosts; contraseñas fuertes y permisos mínimos; actualizar dependencias; proteger admin y respaldar datos.

## Git

Si aún no hay repositorio local:

```powershell
git init
git add .
git commit -m "Preparar despliegue Django en Render"
git branch -M main
git remote add origin https://github.com/<tu-usuario>/<tu-repo>.git
git push -u origin main
```

Actualizaciones posteriores:

```powershell
git add requirements.txt render.yaml rol_api README.md .gitignore
git commit -m "Configurar despliegue Render"
git push
```

## API JWT

`POST /api/login/` recibe username/password y devuelve access/refresh. Envía `Authorization: Bearer <access>` a `/api/me/` y recursos del juego. `POST /api/refresh/` recibe refresh. Login, refresh y authors son públicos; juego requiere token; `/api/users/` requiere rol ADMIN. Crea usuarios mediante `createsuperuser` o `/admin/`.

PowerShell (con servidor activo):

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/login/ -ContentType 'application/json' -Body '{"username":"TU_USUARIO","password":"TU_CLAVE"}'
$headers = @{ Authorization = "Bearer $($login.access)" }
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/me/ -Headers $headers
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/users/ -Headers $headers
```

La entrega requiere URL pública en `/authors`, repo Git público sin secretos y PDF con portada, URL y respuestas al cuestionario. Nombres/códigos y URL GitHub son datos del equipo que debes completar.

