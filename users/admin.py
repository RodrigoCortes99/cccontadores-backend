from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    # Campos que se muestran al editar un usuario
    fieldsets = UserAdmin.fieldsets + (
        (
            "Información de la organización",
            {
                "fields": ("role", "organization"),
            },
        ),
    )

    # Campos que se muestran al crear un usuario
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Información de la organización",
            {
                "fields": ("role", "organization"),
            },
        ),
    )

    # Columnas visibles en la lista de usuarios
    list_display = (
        "username",
        "email",
        "role",
        "organization",
        "is_staff",
        "is_superuser",
    )

    list_filter = (
        "role",
        "organization",
        "is_staff",
        "is_superuser",
    )
