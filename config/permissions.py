# config/permissions.py

from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    """
    Simple role-based permission.
    Expects `request.user.role`.
    """

    allowed_roles: list[str] = []

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and getattr(request.user, "role", None) in self.allowed_roles
        )


class IsCoach(HasRole):
    allowed_roles = ["coach", "admin"]


class IsAnalyst(HasRole):
    allowed_roles = ["analyst", "admin"]


class IsScout(HasRole):
    allowed_roles = ["scout", "coach", "admin"]
