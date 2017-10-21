"""DuckPy URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from mywiki import views
from django.conf import settings

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.view),
    url(r'^edit/$', views.edit),
    url(r'^edit/(?P<title>.*)/$', views.edit),
    url(r'^w/$', views.view),
    url(r'^w/(?P<title>.*)/$', views.view),
    url(r'^raw/$', views.raw),
    url(r'^raw/(?P<title>.*)/$', views.raw),
    url(r'^diff/$', views.diff),
    url(r'^diff/(?P<title>.*)/$', views.diff),
    url(r'^history/$', views.history),
    url(r'^history/(?P<title>.*)/$', views.history),
    url(r'^revert/$', views.revert),
    url(r'^revert/(?P<title>.*)/$', views.revert),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
