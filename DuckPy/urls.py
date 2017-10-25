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
from mywiki import views as wiki_views
from django.conf import settings
from django.contrib.auth import views as auth_views
import LocalSettings

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    
    # 위키 url
    url(r'^$', wiki_views.view),
    url(r'^edit/$', wiki_views.edit),
    url(r'^edit/(?P<title>.*)/$', wiki_views.edit, name='edit'),
    url(r'^w/$', wiki_views.view),
    url(r'^w/(?P<title>.*)/$', wiki_views.view, name='view'),
    url(r'^raw/$', wiki_views.raw),
    url(r'^raw/(?P<title>.*)/$', wiki_views.raw, name='raw'),
    url(r'^diff/$', wiki_views.diff),
    url(r'^diff/(?P<title>.*)/$', wiki_views.diff, name='diff'),
    url(r'^history/$', wiki_views.history),
    url(r'^history/(?P<title>.*)/$', wiki_views.history, name='history'),
    url(r'^revert/$', wiki_views.revert),
    url(r'^revert/(?P<title>.*)/$', wiki_views.revert, name='revert'),
    url(r'^random/$', wiki_views.random, name='random'),
    url(r'^rename/$', wiki_views.random),
    url(r'^rename/(?P<title>.*)/$', wiki_views.rename, name='rename'),
    url(r'^backlink/$', wiki_views.random),
    url(r'^backlink/(?P<title>.*)/$', wiki_views.backlink, name='backlink'),
    url(r'^delete/$', wiki_views.random),
    url(r'^delete/(?P<title>.*)/$', wiki_views.delete, name='delete'),
    
    # 회원 url
    url(r'^login/$', auth_views.login, name='login', kwargs={'template_name': LocalSettings.default_skin + '/login.html'}),
    url(r'^logout/$', auth_views.logout, name='logout', kwargs={'next_page': '/?alert=successLogout'}),
    url(r'^signup/$', wiki_views.signup.as_view(), name='signup'),

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
