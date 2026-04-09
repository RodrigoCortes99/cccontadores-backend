from django.db import models


class Encargo(models.Model):
    class Tipo(models.TextChoices):
        SEGURO_SOCIAL = "seguro_social", "Auditoría para efectos del Seguro Social"
        IMPUESTOS_ESTATALES = "impuestos_estatales", "Auditoría de Impuestos Estatales"
        GUBERNAMENTAL = "gubernamental", "Auditoría Gubernamental"
        CONTABILIDAD_FINANCIERA = "contabilidad_financiera", "Contabilidad Financiera"
        PRECIOS_TRANSFERENCIA = "precios_transferencia", "Precios de Transferencia"
        ASESORIA = "asesoria", "Asesoría"
        COMPLIANCE = "compliance", "Compliance"

    class Estatus(models.TextChoices):
        PLANEACION = "planeacion", "Planeación"
        EJECUCION = "ejecucion", "Ejecución"
        CIERRE = "cierre", "Cierre"
        EMITIDO = "emitido", "Emitido"

    organizacion = models.ForeignKey(
        "core.Organization",
        on_delete=models.PROTECT,
        related_name="encargos",
        verbose_name="Organización",
    )
    cliente = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="encargos",
        verbose_name="Cliente",
    )

    tipo = models.CharField(
        max_length=40,
        choices=Tipo.choices,
        default=Tipo.ASESORIA,
        verbose_name="Tipo",
    )
    estatus = models.CharField(
        max_length=20,
        choices=Estatus.choices,
        default=Estatus.PLANEACION,
        verbose_name="Estatus",
    )

    periodo_inicio = models.DateField(verbose_name="Periodo inicio")
    periodo_fin = models.DateField(verbose_name="Periodo fin")

    nombre = models.CharField(max_length=255, blank=True, default="", verbose_name="Nombre")
    notas = models.TextField(blank=True, default="", verbose_name="Notas")

    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")

    class Meta:
        verbose_name = "Encargo"
        verbose_name_plural = "Encargos"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        etiqueta = self.nombre.strip() or self.get_tipo_display()
        return f"{etiqueta} - {self.cliente.name}"
