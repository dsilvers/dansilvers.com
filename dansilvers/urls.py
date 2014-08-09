from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'dansilvers.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', 'basesite.views.index', name='index'),
    url(r'^about$', 'basesite.views.about', name='about'),
    url(r'^contact$', 'basesite.views.contact', name='contact'),

    url(r'^coding$', 'basesite.views.coding', name='coding'),
    url(r'^photography$', 'basesite.views.photography', name='photography'),

    url(r'^manage/', include(admin.site.urls)),
)
