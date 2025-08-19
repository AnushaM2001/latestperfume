# user_panel/middleware.py

from django.contrib.auth import logout
from django.shortcuts import redirect

class BlockedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated:
            if not user.is_active:  # Or use user.userprofile.is_blocked if applicable
                logout(request)
                return redirect('blocked_user')  # Make sure this URL exists
        return self.get_response(request)
