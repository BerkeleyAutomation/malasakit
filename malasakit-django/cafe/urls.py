"""
cafe URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
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

from django.shortcuts import reverse
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView, RedirectView

from pcari.admin import site
from pcari.urls import api_urlpatterns

# pylint: disable=invalid-name
urlpatterns = [
    # Service worker script served from the `URL_ROOT`
    url(r'^sw.js$',
        TemplateView.as_view(template_name='sw.js',
                             content_type='application/javascript'),
        name='service-worker'),

    # Admin site password reset
    url(r'^admin/password_reset/$', auth_views.password_reset,
        name='admin_password_reset'),
    url(r'^admin/password_reset/done/$', auth_views.password_reset_done,
        name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        auth_views.password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done/$', auth_views.password_reset_complete,
        name='password_reset_complete'),

    # Admin site
    url(r'^admin/', site.urls),

    # AJAX endpoints
    url(r'^api/', include(api_urlpatterns)),
]

# Translate all `pcari` urls
urlpatterns += i18n_patterns(url(r'^', include('pcari.urls')))
urlpatterns += [url(r'^$', RedirectView.as_view(url=reverse('pcari:landing')),
                    name='to-landing')]

# Error handlers
handler404 = 'pcari.views.handle_page_not_found'
handler500 = 'pcari.views.handle_internal_server_error'
