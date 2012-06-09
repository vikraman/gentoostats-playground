from django.conf.urls import patterns, include, url

# Django admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/',     include(admin.site.urls)),

    url(r'^upload/',    include('gentoostats.receiver.urls')),
    url(r'^stats/',     include('gentoostats.stats.urls')),
    url(r'^',           include('gentoostats.main.urls')),

    # TODO:
    #   r'', 'Index',
    #   r'/', 'Index',
    #   r'/arch', 'Arch',
    #   r'/profile', 'Profile',
    #   r'/mirror', 'Mirror',
    #   r'/feature', 'Feature',
    #   r'/keyword', 'Keyword',
    #   r'/repo', 'Repo',
    #   r'/lang', 'Lang',
    #   r'/package/(.+)/(.+)', 'Package',
    #   r'/package/(.+)', 'Package',
    #   r'/package', 'Package',
    #   r'/use/(.+)', 'Use',
    #   r'/use', 'Use',
    #   r'/host/(.+)', 'Host',
    #   r'/host', 'Host',
    #   r'/search', 'Search',
    #   r'/about', 'About'
)
