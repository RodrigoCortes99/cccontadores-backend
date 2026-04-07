from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

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


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        client_id = None
        client_name = None
        if hasattr(user, "client_profile"):
            client_id = user.client_profile.id
            client_name = user.client_profile.name

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "role": getattr(user, "role", None),
                "organization_id": user.organization_id,
                "client_id": client_id,
                "client_name": client_name,
                "is_superuser": user.is_superuser,
            }
        )


class ClientesListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ClienteSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Client.objects.all().order_by("name")

        if user.is_superuser:
            return qs

        if getattr(user, "role", None) == "client":
            if hasattr(user, "client_profile"):
                return qs.filter(id=user.client_profile.id)
            return qs.none()

        if user.organization_id:
            return qs.filter(organization=user.organization)

        return qs.none()


class EncargosListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return EncargoCreateSerializer
        return EncargoSerializer

    def get_queryset(self):
        qs = (
            Encargo.objects.select_related("organizacion", "cliente")
            .all()
            .order_by("-creado_en")
        )

        user = self.request.user

        if user.is_superuser:
            return qs

        if getattr(user, "role", None) == "client":
            if hasattr(user, "client_profile"):
                return qs.filter(cliente=user.client_profile)
            return qs.none()

        if user.organization_id:
            return qs.filter(organizacion=user.organization)

        return qs.none()

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
        encargo_id = self.kwargs["encargo_id"]

        qs = (
            SolicitudPBC.objects.select_related("organizacion", "encargo", "encargo__cliente")
            .filter(encargo_id=encargo_id)
            .order_by("-creado_en")
        )

        user = self.request.user

        if user.is_superuser:
            return qs

        if getattr(user, "role", None) == "client":
            if hasattr(user, "client_profile"):
                return qs.filter(encargo__cliente=user.client_profile)
            return qs.none()

        if user.organization_id:
            return qs.filter(organizacion=user.organization)

        return qs.none()

    def create(self, request, *args, **kwargs):
        encargo_id = self.kwargs["encargo_id"]

        data = request.data.copy()
        data["encargo"] = encargo_id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        solicitud = serializer.save()

        output_serializer = SolicitudPBCSerializer(solicitud)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class DocumentosPBCPorSolicitudListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DocumentoPBCSerializer

    def get_queryset(self):
        solicitud_id = self.kwargs["solicitud_id"]

        qs = (
            DocumentoPBC.objects.select_related(
                "solicitud",
                "subido_por",
                "solicitud__encargo",
                "solicitud__encargo__cliente",
            )
            .filter(solicitud_id=solicitud_id)
            .order_by("-version")
        )

        user = self.request.user

        if user.is_superuser:
            return qs

        if getattr(user, "role", None) == "client":
            if hasattr(user, "client_profile"):
                return qs.filter(solicitud__encargo__cliente=user.client_profile)
            return qs.none()

        if user.organization_id:
            return qs.filter(solicitud__organizacion=user.organization)

        return qs.none()


class SubirDocumentoPBCView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, solicitud_id: int):
        try:
            solicitud = SolicitudPBC.objects.select_related(
                "encargo",
                "encargo__cliente",
            ).get(pk=solicitud_id)
        except SolicitudPBC.DoesNotExist:
            return Response(
                {"detail": "Solicitud PBC no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user

        if not user.is_superuser:
            if getattr(user, "role", None) == "client":
                if not hasattr(user, "client_profile") or solicitud.encargo.cliente_id != user.client_profile.id:
                    return Response(
                        {"detail": "No tienes permiso para subir evidencia a esta solicitud."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            elif user.organization_id:
                if solicitud.organizacion_id != user.organization_id:
                    return Response(
                        {"detail": "No tienes permiso para subir evidencia a esta solicitud."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            else:
                return Response(
                    {"detail": "No tienes permiso para subir evidencia a esta solicitud."},
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
            {
                "id": doc.id,
                "solicitud": solicitud.id,
                "version": doc.version,
                "nombre": doc.nombre,
                "archivo": doc.archivo.url if doc.archivo else None,
                "subido_en": doc.subido_en,
            },
            status=status.HTTP_201_CREATED,
        )


class ActualizarEstatusSolicitudPBCView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, solicitud_id: int):
        try:
            solicitud = SolicitudPBC.objects.select_related(
                "encargo",
                "encargo__cliente",
            ).get(pk=solicitud_id)
        except SolicitudPBC.DoesNotExist:
            return Response(
                {"detail": "Solicitud PBC no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user

        if not user.is_superuser:
            if getattr(user, "role", None) == "client":
                return Response(
                    {"detail": "No tienes permiso para cambiar el estatus de esta solicitud."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if user.organization_id and solicitud.organizacion_id != user.organization_id:
                return Response(
                    {"detail": "No tienes permiso para cambiar el estatus de esta solicitud."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        estatus = ((request.data.get("estatus") or "")).strip().lower()

        estatus_validos = {choice[0] for choice in SolicitudPBC.Estatus.choices}
        if estatus not in estatus_validos:
            return Response(
                {
                    "detail": "Estatus inválido.",
                    "estatus_validos": sorted(list(estatus_validos)),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if estatus == SolicitudPBC.Estatus.RECIBIDO and not solicitud.fecha_recibido:
            solicitud.fecha_recibido = timezone.localdate()

        solicitud.estatus = estatus
        solicitud.save(update_fields=["estatus", "fecha_recibido"])

        return Response(
            {
                "id": solicitud.id,
                "estatus": solicitud.estatus,
                "estatus_display": solicitud.get_estatus_display(),
                "fecha_recibido": solicitud.fecha_recibido,
            },
            status=status.HTTP_200_OK,
        )
