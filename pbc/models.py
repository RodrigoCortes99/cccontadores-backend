from django.conf import settings
from django.db import models


class SolicitudPBC(models.Model):
    class Estatus(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        RECIBIDO = "recibido", "Recibido"
        APROBADO = "aprobado", "Aprobado"
        INCOMPLETO = "incompleto", "Incompleto"

    organizacion = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="solicitudes_pbc",
        verbose_name="Organización",
    )
    encargo = models.ForeignKey(
        "engagements.Encargo",
        on_delete=models.PROTECT,
        related_name="solicitudes_pbc",
        verbose_name="Encargo",
    )

    titulo = models.CharField(max_length=255, verbose_name="Título")
    descripcion = models.TextField(blank=True, default="", verbose_name="Descripción")

    estatus = models.CharField(
        max_length=20,
        choices=Estatus.choices,
        default=Estatus.PENDIENTE,
        verbose_name="Estatus",
    )

    fecha_compromiso = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha compromiso",
    )
    fecha_recibido = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha recibido",
    )

    observaciones_revision = models.TextField(
        blank=True,
        default="",
        verbose_name="Observaciones de revisión",
        help_text="Comentario del auditor para indicar qué falta o qué debe corregirse.",
    )

    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")

    class Meta:
        verbose_name = "Solicitud PBC"
        verbose_name_plural = "Solicitudes PBC"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"{self.titulo} - {self.encargo}"


class DocumentoPBC(models.Model):
    class Estatus(models.TextChoices):
        VIGENTE = "vigente", "Vigente"
        REEMPLAZADO = "reemplazado", "Reemplazado"

    solicitud = models.ForeignKey(
        "pbc.SolicitudPBC",
        on_delete=models.CASCADE,
        related_name="documentos",
        verbose_name="Solicitud",
    )
    version = models.PositiveIntegerField(default=1, verbose_name="Versión")
    nombre = models.CharField(max_length=255, verbose_name="Nombre")
    archivo = models.FileField(upload_to="pbc/", verbose_name="Archivo")
    estatus = models.CharField(
        max_length=20,
        choices=Estatus.choices,
        default=Estatus.VIGENTE,
        verbose_name="Estatus",
    )
    observaciones = models.TextField(blank=True, default="", verbose_name="Observaciones")
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="documentos_pbc_subidos",
        verbose_name="Subido por",
    )
    subido_en = models.DateTimeField(auto_now_add=True, verbose_name="Subido en")

    class Meta:
        verbose_name = "Documento PBC"
        verbose_name_plural = "Documentos PBC"
        ordering = ["-subido_en"]

    def __str__(self) -> str:
        return f"{self.nombre} v{self.version}"
