from django.utils.cache import add_never_cache_headers

class DisableClientSideCachingMiddleware:
    """
    Middleware to ensure that the browser does not cache any pages.
    This strictly prevents a user from hitting the 'Back' button after logging out
    and viewing previously loaded sensitive pages. They will be forced to log in again.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Add headers to strictly disable caching
        add_never_cache_headers(response)
        return response
