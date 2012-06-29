from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView

urlpatterns = patterns('gentoostats.main.views',
    url( r'^(?:index(?:\.html)?)?$'
       , TemplateView.as_view(template_name='main/index.html')
       , name='index_url'
    ),
)
