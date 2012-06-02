from django.conf.urls import patterns, include, url

urlpatterns = patterns('gentoostats.main.views',
    url(r'^(?:index/)?$', 'index', name='index'),
)
