"""Middleware for Achieve."""

import pytz
from django.utils import timezone


class TimezoneMiddleware(object):  # pragma: no cover
    """Middleware to apply user time zone."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated():
            tzname = request.user.achieveprofile.timezone
            if tzname:
                timezone.activate(pytz.timezone(tzname))
            else:
                timezone.deactivate()

        response = self.get_response(request)
        return response
