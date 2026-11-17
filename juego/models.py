from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = [("USER", "User"), ("ADMIN", "Admin")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="USER")

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Usuario(models.Model):
    nombre_usuario = models.CharField(max_length=100, unique=True)
    # Campo de demostración del modelo del taller; no usar texto plano para autenticación real.
    contrasena = models.CharField(max_length=128)
    correo = models.EmailField(unique=True)

    def __str__(self):
        return self.nombre_usuario


class Perfil(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="perfil")
    biografia = models.TextField(blank=True)
    avatar = models.URLField(blank=True)

    def __str__(self):
        return f"Perfil de {self.usuario.nombre_usuario}"


class Personaje(models.Model):
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="personajes")
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50, default="aventurero")
    descripcion = models.TextField(blank=True)
    ataque = models.PositiveIntegerField(default=0)
    defensa = models.PositiveIntegerField(default=0)
    estamina = models.PositiveIntegerField(default=0)
    habilidades = models.ManyToManyField("Habilidad", through="PersonajeHabilidad", related_name="personajes")

    def __str__(self):
        return self.nombre

    def atributos_efectivos(self):
        """Atributos base más el incremento de cada habilidad multiplicado por su nivel."""
        ataque, defensa, estamina = self.ataque, self.defensa, self.estamina
        for relacion in self.personajehabilidad_set.select_related("habilidad"):
            habilidad, nivel = relacion.habilidad, relacion.nivel
            ataque += habilidad.incremento_ataque * nivel
            defensa += habilidad.incremento_defensa * nivel
            estamina += habilidad.incremento_estamina * nivel
        return {"ataque": ataque, "defensa": defensa, "estamina": estamina}


class Habilidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    # Los incrementos pueden ser negativos, como en los datos de la actividad 08.1.
    incremento_ataque = models.IntegerField(default=0)
    incremento_defensa = models.IntegerField(default=0)
    incremento_estamina = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre


class PersonajeHabilidad(models.Model):
    personaje = models.ForeignKey(Personaje, on_delete=models.CASCADE)
    habilidad = models.ForeignKey(Habilidad, on_delete=models.CASCADE)
    nivel = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["personaje", "habilidad"], name="unica_habilidad_por_personaje")]

    def __str__(self):
        return f"{self.personaje} - {self.habilidad} (nivel {self.nivel})"


class RequestLog(models.Model):
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    ip = models.GenericIPAddressField(null=True, blank=True)
    called_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "request_log"
        ordering = ["-called_at"]

    def __str__(self):
        return f"{self.method} {self.path} ({self.called_at})"
