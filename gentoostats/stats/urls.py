from django.conf.urls import patterns, include, url

urlpatterns = patterns('gentoostats.stats.views',
    # TODO: this needs updating.

    url(r'^host/(?P<id>\w+)/$', 'host_details',  name='host_details_url'),
    url(r'^$',                  'overall_stats', name='overall_stats_url'),
)
