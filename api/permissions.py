from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Объектное разрешение: разрешить запись только владельцу.
    Чтение разрешено всем .
    """

    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS это GET, HEAD, OPTIONS
        if request.method in permissions.SAFE_METHODS:
            return True

        # Для POST/PUT/PATCH/DELETE проверяем владельца
        return obj.owner == request.user
