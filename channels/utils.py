from __future__ import unicode_literals

from functools import wraps
from django.utils.decorators import available_attrs

# This middleware allows us to short circuit middleware processing for views
# that are decorated with @disable_middleware.
#
# We use this for some of our API views, specifically ones coming in from aggregators
# where most of the middlewares are not useful to us.


def disable_middleware(view_func):
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)
    wrapped_view.disable_middleware = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)