from workers import WorkerEntrypoint
import asgi

from api import app, CLIENT_TIMEZONE


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Cloudflare detects the visitor's timezone (request.cf.timezone).
        # Store it for this request so the API can use it when no ?tz= is given.
        cf = getattr(request, "cf", None)
        tz = getattr(cf, "timezone", None) if cf else None
        token = CLIENT_TIMEZONE.set(tz)
        try:
            return await asgi.fetch(app, request, self.env)
        finally:
            CLIENT_TIMEZONE.reset(token)

