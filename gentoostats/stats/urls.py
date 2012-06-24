from django.conf.urls import patterns, include, url

urlpatterns = patterns('gentoostats.stats.views',
    # TODO: this needs updating.

    url(r'^host/(?P<host_id>[0-9\-a-fA-F]+)/?$', 'host_details',  name='host_details_url'),
    url(r'^$',                                 'overall_stats', name='overall_stats_url'),

    # url(r'^arch', 'Arch',
    # url(r'^profile', 'Profile',
    # url(r'^mirror', 'Mirror',
    # url(r'^feature', 'Feature',
    # url(r'^keyword', 'Keyword',
    # url(r'^repo', 'Repo',
    # url(r'^lang', 'Lang',
    # url(r'^package/(.+)/(.+)', 'Package',
    # url(r'^package/(.+)', 'Package',
    # url(r'^package', 'Package',
    # url(r'^use/(.+)', 'Use',
    # url(r'^use', 'Use',
    # url(r'^host/(.+)', 'Host',
    # url(r'^host', 'Host',
)
