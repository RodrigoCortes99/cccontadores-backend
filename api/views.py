from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from clients.models import Client
from engagements.models import Encargo
from pbc.models import DocumentoPBC, SolicitudPBC

from .serializers import (
    ClienteSerializer,
    DocumentoPBCSerializer,
    EncargoCreateSerializer,
    EncargoSerializer,
    SolicitudPBCCreateSerializer,
    SolicitudPBCSerializer,
)


class ClientesListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ClienteSerializer

    def get_queryset(self):
        user = self.request.user

        if getattr(user, "is_superuser", False):
            return Client.objects.all().order_by("name")

        if getattr(user, "role", None) == "client" and hasattr(user, "client_profile"):
            return Client.objects.filter(pk=user.client_profile.pk).order_by("name")

        if getattr(user, "organization_id", None):
            return Client.objects.filter(organization_id=user.organization_id).order_by("name")

        return Client.objects.none()


class EncargosListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return EncargoCreateSerializer
        return EncargoSerializer

    def get_queryset(self):
        user = self.request.user

        queryset = Encargo.objects.select_related("organizacion", "cliente").all()

        if getattr(user, "is_superuser", False):
            return queryset.order_by("-creado_en")

        if getattr(user, "role", None) == "client" and hasattr(user, "client_profile"):
            return queryset.filter(cliente_id=user.client_profile.pk).order_by("-creado_en")

        if getattr(user, "organization_id", None):
            return queryset.filter(organizacion_id=user.organization_id).order_by("-creado_en")

        return Encargo.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        encargo = serializer.save()

        output_serializer = EncargoSerializer(encargo)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class SolicitudesPBCPorEncargoListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SolicitudPBCCreateSerializer
        return SolicitudPBCSerializer

    def get_queryset(self):
        user = self.request.user
        encargo_id = self.kwargs["encargo_id"]

        queryset = SolicitudPBC.objects.select_related("organizacion", "encargo").filter(
            encargo_id=encargo_id
        )

        if getattr(user, "is_superuser", False):
            return queryset.order_by("-creado_en")

        if getattr(user, "role", None) == "client" and hasattr(user, "client_profile"):
            return queryset.filter(encargo__cliente_id=user.client_profile.pk).order_by("-creado_en")

        if getattr(user, "organization_id", None):
            return queryset.filter(organizacion_id=user.organization_id).order_by("-creado_en")

        return SolicitudPBC.objects.none()

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["encargo"] = self.kwargs["encargo_id"]

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        solicitud = serializer.save()

        output_serializer = SolicitudPBCSerializer(solicitud)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class DocumentosPBCPorSolicitudListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DocumentoPBCSerializer

    def get_queryset(self):
        user = self.request.user
        solicitud_id = self.kwargs["solicitud_id"]

        queryset = DocumentoPBC.objects.select_related("solicitud", "subido_por").filter(
            solicitud_id=solicitud_id
        )

        if getattr(user, "is_superuser", False):
            return queryset.order_by("-version")

        if getattr(user, "role", None) == "client" and hasattr(user, "client_profile"):
            return queryset.filter(solicitud__encargo__cliente_id=user.client_profile.pk).order_by(
                "-version"
            )

        if getattr(user, "organization_id", None):
            return queryset.filter(solicitud__organizacion_id=user.organization_id).order_by(
                "-version"
            )

        return DocumentoPBC.objects.none()


class SubirDocumentoPBCView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, solicitud_id: int):
        try:
            solicitud = SolicitudPBC.objects.select_related("encargo").get(pk=solicitud_id)
        except SolicitudPBC.DoesNotExist:
            return Response(
                {"detail": "Solicitud PBC no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user

        if not getattr(user, "is_superuser", False):
            if getattr(user, "role", None) == "client" and hasattr(user, "client_profile"):
                if solicitud.encargo.cliente_id != user.client_profile.pk:
                    return Response(
                        {"detail": "No tienes permiso para subir documentos a esta solicitud."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            elif getattr(user, "organization_id", None):
                if solicitud.organizacion_id != user.organization_id:
                    return Response(
                        {"detail": "No tienes permiso para subir documentos a esta solicitud."},
                        status=status.HTTP_403_FORBIDDEN,
                    )

        archivo = request.FILES.get("archivo")
        if not archivo:
            return Response(
                {"detail": "Falta el archivo. Usa el campo 'archivo'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        nombre = (request.data.get("nombre") or "").strip() or archivo.name
        observaciones = (request.data.get("observaciones") or "").strip()

        last_version = (
            DocumentoPBC.objects.filter(solicitud=solicitud)
            .order_by("-version")
            .values_list("version", flat=True)
            .first()
        )
        next_version = (last_version or 0) + 1

        doc = DocumentoPBC.objects.create(
            solicitud=solicitud,
            version=next_version,
            nombre=nombre,
            archivo=archivo,
            observaciones=observaciones,
            subido_por=request.user,
        )

        if solicitud.estatus != SolicitudPBC.Estatus.APROBADO:
            solicitud.estatus = SolicitudPBC.Estatus.RECIBIDO

            if not solicitud.fecha_recibido:
                solicitud.fecha_recibido = timezone.localdate()

            solicitud.save(update_fields=["estatus", "fecha_recibido"])

        return Response(
            DocumentoPBCSerializer(doc).data,
            status=status.HTTP_201_CREATED,
        )


class ActualizarEstatusSolicitudPBCView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, solicitud_id: int):
        try:
            solicitud = SolicitudPBC.objects.get(pk=solicitud_id)
        except SolicitudPBC.DoesNotExist:
            return Response(
                {"detail": "Solicitud PBC no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        estatus = ((request.data.get("estatus") or "")).strip().lower()
        observaciones_revision = (request.data.get("observaciones_revision") or "").strip()

        estatus_validos = {choice[0] for choice in SolicitudPBC.Estatus.choices}
        if estatus not in estatus_validos:
            return Response(
                {
                    "detail": "Estatus inválido.",
                    "estatus_validos": sorted(list(estatus_validos)),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if estatus == SolicitudPBC.Estatus.INCOMPLETO and not observaciones_revision:
            return Response(
                {
                    "detail": "Debes escribir una observación cuando marques la solicitud como incompleta."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if estatus == SolicitudPBC.Estatus.RECIBIDO and not solicitud.fecha_recibido:
            solicitud.fecha_recibido = timezone.localdate()

        if estatus != SolicitudPBC.Estatus.INCOMPLETO and observaciones_revision == "":
            observaciones_revision = solicitud.observaciones_revision

        solicitud.estatus = estatus
        solicitud.observaciones_revision = observaciones_revision
        solicitud.save(update_fields=["estatus", "fecha_recibido", "observaciones_revision"])

        return Response(
            {
                "id": solicitud.id,
                "estatus": solicitud.estatus,
                "estatus_display": solicitud.get_estatus_display(),
                "fecha_recibido": solicitud.fecha_recibido,
                "observaciones_revision": solicitud.observaciones_revision,
            },
            status=status.HTTP_200_OK,
        )
