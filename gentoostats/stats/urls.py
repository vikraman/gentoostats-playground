from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView
from django.core.urlresolvers import reverse_lazy

urlpatterns = patterns('gentoostats.stats.views',
    url( r'^$'
       , 'index'
       , name='index_url'
    ),

    url( r'^about/$'
       , 'about'
       , name='about_url'
    ),

    url( r'^overall/$'
       , 'overall_stats'
       , name='overall_stats_url'
    ),

    url( r'^host_search/$'
       , 'host_search'
       , name='host_search_url'
    ),

    url( r'^host/$'
       , 'host_stats'
       , name='host_stats_url'
    ),

    url( r'^host/(?P<host_id>[\da-fA-F]{8}-?[\da-fA-F]{4}-?[\da-fA-F]{4}-?[\da-fA-F]{4}-?[\da-fA-F]{12})/$'
       , 'host_details'
       , name='host_details_url'
    ),

    url( r'^arch/$'
       , 'arch_stats'
       , name='arch_stats_url'
    ),

    url( r'^arch/(?P<arch>\w+)/'
       , 'arch_details'
       , name='arch_details_url'
    ),

    url( r'^feature/$'
       , 'feature_stats'
       , name='feature_stats_url'
    ),

    url( r'^feature/(?P<feature>\S+)/'
       , 'feature_details'
       , name='feature_details_url'
    ),

    url( r'^keyword/$'
       , 'keyword_stats'
       , name='keyword_stats_url'
    ),

    url( r'^keyword/(?P<keyword>\w+)/'
       , 'keyword_details'
       , name='keyword_details_url'
    ),

    url( r'^repository/$'
       , 'repository_stats'
       , name='repository_stats_url'
    ),

    url( r'^repository/(?P<repository>\S+)/'
       , 'repository_details'
       , name='repository_details_url'
    ),

    url( r'^mirror/$'
       , 'mirror_stats'
       , name='mirror_stats_url'
    ),

    url( r'^mirror/(?P<mirror>\S+)/'
       , 'mirror_details'
       , name='mirror_details_url'
    ),

    url( r'^sync/$'
       , 'sync_stats'
       , name='sync_stats_url'
    ),

    url( r'^sync/(?P<sync>\S+)/'
       , 'sync_details'
       , name='sync_details_url'
    ),

    url( r'^profile/$'
       , 'profile_stats'
       , name='profile_stats_url'
    ),

    url( r'^profile/(?P<profile>\S+)/'
       , 'profile_details'
       , name='profile_details_url'
    ),

    url( r'^lang/$'
       , 'lang_stats'
       , name='lang_stats_url'
    ),

    url( r'^lang/(?P<lang>\S+)/'
       , 'lang_details'
       , name='lang_details_url'
    ),

    url( r'^category/$'
       , 'category_stats'
       , name='category_stats_url'
    ),

    url( r'^category/(?P<category>\S+)/'
       , 'category_details'
       , name='category_details_url'
    ),

    url( r'^submission/$'
       , 'submission_stats'
       , name='submission_stats_url'
    ),

    url( r'^submission/(?P<submission>\S+)/'
       , 'submission_details'
       , name='submission_details_url'
    ),

    url( r'^use/$'
       , 'useflag_stats'
       , name='useflag_stats_url'
    ),

    url( r'^use/(?P<useflag>\S+)/'
       , 'useflag_details'
       , name='useflag_details_url'
    ),

    # TODO: /package/

    # TODO: Redirect /features/... to /feature/...
    url( r'^features/$'
       , RedirectView.as_view(url=reverse_lazy('feature_stats_url'))
    ),
)
