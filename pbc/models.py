from django.conf import settings
from django.db import models


class SolicitudPBC(models.Model):
    class Estatus(models.TextChoices):
        SOLICITADO = "solicitado", "Solicitado"
        RECIBIDO = "recibido", "Recibido"
        INCOMPLETO = "incompleto", "Incompleto"
        APROBADO = "aprobado", "Aprobado"

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
        default=Estatus.SOLICITADO,
        verbose_name="Estatus",
    )

    fecha_compromiso = models.DateField(null=True, blank=True, verbose_name="Fecha compromiso")
    fecha_recibido = models.DateField(null=True, blank=True, verbose_name="Fecha recibido")

    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")

    class Meta:
        verbose_name = "Solicitud PBC"
        verbose_name_plural = "Solicitudes PBC"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"{self.titulo} ({self.get_estatus_display()})"


class DocumentoPBC(models.Model):
    class EstatusDocumento(models.TextChoices):
        RECIBIDO = "recibido", "Recibido"
        EN_REVISION = "en_revision", "En revisión"
        OBSERVADO = "observado", "Observado"
        APROBADO = "aprobado", "Aprobado"

    solicitud = models.ForeignKey(
        "pbc.SolicitudPBC",
        on_delete=models.CASCADE,
        related_name="documentos",
        verbose_name="Solicitud PBC",
    )

    # Versionado automático: 1,2,3... por solicitud
    version = models.PositiveIntegerField(verbose_name="Versión")

    archivo = models.FileField(upload_to="pbc/", verbose_name="Archivo")
    nombre = models.CharField(max_length=255, blank=True, default="", verbose_name="Nombre (opcional)")

    estatus = models.CharField(
        max_length=20,
        choices=EstatusDocumento.choices,
        default=EstatusDocumento.RECIBIDO,
        verbose_name="Estatus del documento",
    )

    observaciones = models.TextField(blank=True, default="", verbose_name="Observaciones del auditor")

    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="documentos_pbc",
        verbose_name="Subido por",
    )
    subido_en = models.DateTimeField(auto_now_add=True, verbose_name="Subido en")

    class Meta:
        verbose_name = "Documento PBC"
        verbose_name_plural = "Documentos PBC"
        ordering = ["-subido_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["solicitud", "version"],
                name="unique_version_por_solicitud",
            )
        ]

    def __str__(self) -> str:
        base = self.nombre.strip() or self.archivo.name
        return f"v{self.version} - {base}"
