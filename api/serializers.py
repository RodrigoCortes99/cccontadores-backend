from rest_framework import serializers

from clients.models import Client
from core.models import Organization
from engagements.models import Encargo
from pbc.models import SolicitudPBC, DocumentoPBC


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id", "name"]


class EncargoSerializer(serializers.ModelSerializer):
    organizacion = serializers.StringRelatedField()
    cliente = serializers.StringRelatedField()
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    estatus_display = serializers.CharField(source="get_estatus_display", read_only=True)

    class Meta:
        model = Encargo
        fields = [
            "id",
            "organizacion",
            "cliente",
            "tipo",
            "tipo_display",
            "estatus",
            "estatus_display",
            "periodo_inicio",
            "periodo_fin",
            "nombre",
            "notas",
            "creado_en",
        ]


class EncargoCreateSerializer(serializers.ModelSerializer):
    organizacion = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())
    cliente = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())

    class Meta:
        model = Encargo
        fields = [
            "organizacion",
            "cliente",
            "tipo",
            "estatus",
            "periodo_inicio",
            "periodo_fin",
            "nombre",
            "notas",
        ]


class SolicitudPBCSerializer(serializers.ModelSerializer):
    organizacion = serializers.StringRelatedField()
    encargo = serializers.StringRelatedField()
    estatus_display = serializers.CharField(source="get_estatus_display", read_only=True)

    class Meta:
        model = SolicitudPBC
        fields = [
            "id",
            "organizacion",
            "encargo",
            "titulo",
            "descripcion",
            "estatus",
            "estatus_display",
            "fecha_compromiso",
            "fecha_recibido",
            "creado_en",
        ]


class SolicitudPBCCreateSerializer(serializers.ModelSerializer):
    organizacion = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())
    encargo = serializers.PrimaryKeyRelatedField(queryset=Encargo.objects.all())

    class Meta:
        model = SolicitudPBC
        fields = [
            "organizacion",
            "encargo",
            "titulo",
            "descripcion",
            "estatus",
            "fecha_compromiso",
        ]


class DocumentoPBCSerializer(serializers.ModelSerializer):
    solicitud = serializers.PrimaryKeyRelatedField(read_only=True)
    archivo = serializers.SerializerMethodField()
    estatus_display = serializers.CharField(source="get_estatus_display", read_only=True)
    subido_por = serializers.StringRelatedField()

    class Meta:
        model = DocumentoPBC
        fields = [
            "id",
            "solicitud",
            "version",
            "nombre",
            "archivo",
            "estatus",
            "estatus_display",
            "observaciones",
            "subido_por",
            "subido_en",
        ]

    def get_archivo(self, obj):
        if obj.archivo:
            return obj.archivo.url
        return None
