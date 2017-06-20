"""cafe URL Configuration

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
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth import views as auth_views
from django.contrib import admin

from django.views.generic import TemplateView

# pylint: disable=invalid-name
urlpatterns = [
    # ServiceWorker script- special case
    url(r'^sw.js$',
        TemplateView.as_view(template_name='sw.js',
                             content_type='application/javascript'),
        name='sw.js'),


    # Admin site password reset
    url(r'^admin/password_reset/', auth_views.password_reset, name='admin_password_reset'),
    url(r'^admin/password_reset/done/', auth_views.password_reset_done, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/', auth_views.password_reset_confirm,
        name='password_reset_confirm'),
    url(r'^reset/done/', auth_views.password_reset_complete, name='password_reset_complete'),

    # Admin site
    url(r'^admin/', admin.site.urls),
]

# Translate all pcari urls
urlpatterns += i18n_patterns(url(r'^', include('pcari.urls')))
