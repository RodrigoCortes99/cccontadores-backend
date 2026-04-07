from django.contrib import admin
from .models import SolicitudPBC, DocumentoPBC


class DocumentoPBCInline(admin.TabularInline):
    model = DocumentoPBC
    extra = 0
    fields = ("version", "archivo", "nombre", "estatus", "observaciones", "subido_por", "subido_en")
    readonly_fields = ("subido_en", "subido_por")


@admin.register(SolicitudPBC)
class SolicitudPBCAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "encargo",
        "organizacion",
        "estatus",
        "fecha_compromiso",
        "fecha_recibido",
        "creado_en",
        "conteo_documentos",
    )
    list_filter = ("organizacion", "estatus")
    search_fields = (
        "titulo",
        "descripcion",
        "encargo__nombre",
        "encargo__cliente__name",
    )
    readonly_fields = ("creado_en",)
    inlines = [DocumentoPBCInline]

    def conteo_documentos(self, obj):
        return obj.documentos.count()

    conteo_documentos.short_description = "Docs"


@admin.register(DocumentoPBC)
class DocumentoPBCAdmin(admin.ModelAdmin):
    list_display = ("id", "solicitud", "version", "estatus", "subido_por", "subido_en")
    list_filter = ("estatus", "subido_por")
    search_fields = ("solicitud__titulo", "archivo", "nombre", "observaciones")
    readonly_fields = ("subido_en",)

    def save_model(self, request, obj, form, change):
        if not obj.subido_por_id:
            obj.subido_por = request.user
        super().save_model(request, obj, form, change)
