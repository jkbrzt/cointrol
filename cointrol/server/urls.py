"""
Main URLs file

"""
import os

from django.contrib import admin
from django.conf import settings
from django.conf.urls import url, include, patterns
from django.contrib.auth import logout
from django.http import HttpResponse
from django.shortcuts import redirect

from .api.urls import urlpatterns as api_urls


admin.autodiscover()


INDEX_FILE_PATH = os.path.join(settings.WEBAPP_STATIC_DIR, 'index.html')


def index_view(request):
    if request.user.is_authenticated():
        with open(INDEX_FILE_PATH, 'r') as index:
            return HttpResponse(index.read())
    else:
        return HttpResponse('<a href="/admin/login/?next=/">Log in</a>')


def logout_view(request):
    logout(request)
    return redirect('/')


def error_view(request):
    raise RuntimeError('test exception')


urlpatterns = patterns(
    '',
    url(r'^$', index_view),
    url(r'^error$', error_view),
    url(r'^logout$', logout_view),
    url(r'^admin/', include(admin.site.urls)),
    url('^api/', include(api_urls)),
)
