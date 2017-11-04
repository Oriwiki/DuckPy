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
from django.conf.urls import include, url, handler404, handler403
from django.contrib import admin
from mywiki import views as wiki_views
from django.conf import settings
from django.contrib.auth import views as auth_views
import LocalSettings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('mywiki.urls')),
    
    # 회원
    url(r'^login/$', auth_views.login, name='login', kwargs={'template_name': LocalSettings.default_skin + '/login.html'}),
    url(r'^logout/$', auth_views.logout, name='logout', kwargs={'next_page': '/?alert=successLogout'}),
    url(r'^signup/$', wiki_views.signup.as_view(), name='signup'),

]

handler404 = wiki_views.page_not_found
handler403 = wiki_views.permission_denied

# if settings.DEBUG:
import debug_toolbar
urlpatterns = [
    url(r'^__debug__/', include(debug_toolbar.urls)),
] + urlpatterns
