from django.conf.urls import patterns, include, url

urlpatterns = patterns('gentoostats.receiver.views',
    # NOTE: A redirect issued by Django's APPEND_SLASH will lead to the loss of
    # POST data. That's why I explicitly support both /upload and /upload/ in my
    # url pattern.

    url( r'^/?$'
       , 'accept_submission'
       , name='accept_submission_url'
    ),
)
