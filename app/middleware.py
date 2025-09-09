from django.shortcuts import redirect
from django.contrib import messages
from social_core.exceptions import AuthCanceled

class SocialAuthExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, AuthCanceled):
            messages.error(request, "You cancelled Google login. Please try again.")
            return redirect('login')
        return None
