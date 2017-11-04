from django.conf.urls import url
from .views import *
import LocalSettings
from django.core.urlresolvers import reverse_lazy
from django.views.generic.base import RedirectView


frontpage = LocalSettings.project_name + ':' + LocalSettings.mainpage_title

urlpatterns = [
    url(r'^$', RedirectView.as_view(url=reverse_lazy('view', kwargs={'title': frontpage}))),
    url(r'^w/$', RedirectView.as_view(url=reverse_lazy('view', kwargs={'title': frontpage}))),
    url(r'^w/(?P<title>.*)/$', WikiView.as_view(), name='view'),
    url(r'^edit/$', RedirectView.as_view(url=reverse_lazy('view', kwargs={'title': frontpage}))),
    url(r'^edit/(?P<title>.*)/$', EditView.as_view(), name='edit'),
    url(r'^raw/$', RedirectView.as_view(url=reverse_lazy('view', kwargs={'title': frontpage}))),
    url(r'^raw/(?P<title>.*)/$', RawView.as_view(), name='raw'),
    url(r'^diff/$', RedirectView.as_view(url=reverse_lazy('view', kwargs={'title': frontpage}))),
    url(r'^diff/(?P<title>.*)/$', DiffView.as_view(), name='diff'),
    url(r'^history/$', RedirectView.as_view(url=reverse_lazy('view', kwargs={'title': frontpage}))),
    url(r'^history/(?P<title>.*)/$', HistoryView.as_view(), name='history'),
    url(r'^revert/$', RedirectView.as_view(url=reverse_lazy('view', kwargs={'title': frontpage}))),
    url(r'^revert/(?P<title>.*)/$', RevertView.as_view(), name='revert'),
    url(r'^random/$', random, name='random'),
    url(r'^rename/$', RedirectView.as_view(url=reverse_lazy('view', kwargs={'title': frontpage}))),
    url(r'^rename/(?P<title>.*)/$', RenameView.as_view(), name='rename'),
    url(r'^backlink/$', RedirectView.as_view(url=reverse_lazy('view', kwargs={'title': frontpage}))),
    url(r'^backlink/(?P<title>.*)/$', BacklinkView.as_view(), name='backlink'),
    url(r'^delete/$', RedirectView.as_view(url=reverse_lazy('view', kwargs={'title': frontpage}))),
    url(r'^delete/(?P<title>.*)/$', DeleteView.as_view(), name='delete'),
    url(r'^contribution/$', RedirectView.as_view(url=reverse_lazy('view', kwargs={'title': frontpage}))),
    url(r'^contribution/(?P<editor>.*)/$', ContributionView.as_view(), name='contribution'),
    url(r'^recentchanges/$', RecentChangesView.as_view(), name='recentchanges'),
    url(r'^acl/$', RedirectView.as_view(url=reverse_lazy('view', kwargs={'title': frontpage}))),
    url(r'^acl/(?P<title>.*)/$', ACLView.as_view(), name='acl'),
    url(r'^upload/$', UploadView.as_view(), name='upload'),
]