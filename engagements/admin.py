from django.contrib import admin
from .models import Encargo


@admin.register(Encargo)
class EncargoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "cliente",
        "organizacion",
        "tipo",
        "estatus",
        "periodo_inicio",
        "periodo_fin",
        "creado_en",
    )
    list_filter = ("organizacion", "tipo", "estatus")
    search_fields = ("nombre", "cliente__name")
