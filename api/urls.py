from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    CurrentUserView,
    ClientesListView,
    OrganizacionesListView,
    EncargosListView,
    SolicitudesPBCPorEncargoListView,
    DocumentosPBCPorSolicitudListView,
    SubirDocumentoPBCView,
    ActualizarEstatusSolicitudPBCView,
)

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", CurrentUserView.as_view(), name="current_user"),
    path("clientes/", ClientesListView.as_view(), name="clientes_list"),
    path("encargos/", EncargosListView.as_view(), name="encargos_list"),
    path("organizaciones/", OrganizacionesListView.as_view(), name="organizaciones-list"),
    path("encargos/<int:encargo_id>/pbc/", SolicitudesPBCPorEncargoListView.as_view(), name="pbc_por_encargo"),
    path("pbc/<int:solicitud_id>/documentos/", DocumentosPBCPorSolicitudListView.as_view(), name="documentos_pbc_por_solicitud"),
    path("pbc/<int:solicitud_id>/documentos/subir/", SubirDocumentoPBCView.as_view(), name="subir_documento_pbc"),
    path("pbc/<int:solicitud_id>/estatus/", ActualizarEstatusSolicitudPBCView.as_view(), name="pbc_actualizar_estatus"),
]
