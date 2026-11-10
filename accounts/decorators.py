from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def redirect_by_role(user):
    if user.role == user.Role.ADMIN or (user.is_staff and user.role not in ("doctor", "patient")):
        return redirect("admin:index")
    if user.role == user.Role.DOCTOR:
        return redirect("doctors:dashboard")
    return redirect("patients:dashboard")


def role_required(role):
    """Require a logged-in user with the given role; send everyone else to their own dashboard."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.user.role != role:
                return redirect_by_role(request.user)
            return view(request, *args, **kwargs)

        return login_required(wrapper)

    return decorator
