from django.conf.urls import url
from django.contrib import admin

from channels.views import FacebookHandler

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^facebook/handler$', FacebookHandler.as_view(), name='handlers.facebook_handler'),
]
