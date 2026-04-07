from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "organization",
        "user",
        "rfc",
        "industry",
        "is_active",
        "created_at",
    )
    list_filter = ("organization", "is_active")
    search_fields = ("name", "rfc", "industry", "user__username")
