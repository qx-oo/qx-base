from rest_framework.permissions import (
    AllowAny, IsAuthenticated, BasePermission
)


def action_authenticated(allow_actions=[]):
    """
    allow_actions: need auth action views.
    """

    class ViewSetPerm(BasePermission):

        def has_permission(self, request, view):
            if view.action in allow_actions:
                return AllowAny().has_permission(request, view)
            return IsAuthenticated().has_permission(request, view)

    return ViewSetPerm
