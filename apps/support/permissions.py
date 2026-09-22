from rest_framework.permissions import BasePermission


class IsTicketOwner(BasePermission):
    message = "شما به این تیکت دسترسی ندارید."

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id


class IsSupportAgent(BasePermission):
    message = "شما دسترسی پشتیبانی ندارید."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_staff
        )