from .models import ActivityLog


class ActivityLogMiddleware:
    ignored_prefixes = ("/static/", "/media/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        response = self.get_response(request)

        if (
            user
            and user.is_authenticated
            and request.method != "GET"
            and not request.path.startswith(self.ignored_prefixes)
        ):
            ActivityLog.objects.create(
                user=user,
                action=getattr(request, "activity_log_action", request.method),
                path=request.path,
                status_code=response.status_code,
                ip_address=self._get_ip_address(request),
                details=getattr(
                    request,
                    "activity_log_description",
                    f"{request.method} request completed with status "
                    f"{response.status_code}.",
                ),
            )

        return response

    @staticmethod
    def _get_ip_address(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
