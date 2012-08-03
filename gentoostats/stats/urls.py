from tastypie.api import Api

from django.conf.urls import patterns, include, url

from .api import *

api = Api(api_name='')
api.register(HostResource())
api.register(SubmissionResource())

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

    # Host(s): #{{{
    url( r'^host/$'
       , 'host_search'
       , name='host_search_url'
    ),

    url( r'^(?:host/)(?P<host_id>[\da-fA-F]{8}-?[\da-fA-F]{4}-?[\da-fA-F]{4}-?[\da-fA-F]{4}-?[\da-fA-F]{12})/$'
       , 'host_details'
       , name='host_details_url'
    ),
    #}}}

    # ARCH(es): #{{{
    url( r'^arch/(?P<arch>\w+)/'
       , 'arch_details'
       , name='arch_details_url'
    ),
    #}}}

    # FEATURE(s): #{{{
    url( r'^feature/(?P<feature>\S+)/'
       , 'feature_details'
       , name='feature_details_url'
    ),
    #}}}

    # Keyword(s): #{{{
    url( r'^keyword/(?P<keyword>\w+)/'
       , 'keyword_details'
       , name='keyword_details_url'
    ),
    #}}}

    # Repository(ies): #{{{
    url( r'^repository/$'
       , 'repository_stats'
       , name='repository_stats_url'
    ),

    url( r'^repository/(?P<repository>\S+)/'
       , 'repository_details'
       , name='repository_details_url'
    ),
    #}}}

    # Mirror(s): #{{{
    url( r'^mirror/$'
       , 'mirror_stats'
       , name='mirror_stats_url'
    ),

    url( r'^mirror/(?P<mirror>\S+)/'
       , 'mirror_details'
       , name='mirror_details_url'
    ),
    #}}}

    # SYNC(s): #{{{
    url( r'^sync/$'
       , 'sync_stats'
       , name='sync_stats_url'
    ),

    url( r'^sync/(?P<sync>\S+)/'
       , 'sync_details'
       , name='sync_details_url'
    ),
    #}}}

    # Profile(s): #{{{
    url( r'^profile/(?P<profile>\S+)/'
       , 'profile_details'
       , name='profile_details_url'
    ),
    #}}}

    # LANG(s): #{{{
    url( r'^lang/(?P<lang>\S+)/'
       , 'lang_details'
       , name='lang_details_url'
    ),
    #}}}

    # Category(ies): #{{{
    url( r'^category/$'
       , 'category_stats'
       , name='category_stats_url'
    ),

    url( r'^category/(?P<category>\S+)/'
       , 'category_details'
       , name='category_details_url'
    ),
    #}}}

    # Submission(s): #{{{
    url( r'^submission/(?P<id>\d+)/'
       , 'submission_details'
       , name='submission_details_url'
    ),
    #}}}

    # USE flag(s): #{{{
    url( r'^use/$'
       , 'useflag_stats'
       , name='useflag_stats_url'
    ),

    url( r'^use/(?P<useflag>\S+)/'
       , 'useflag_details'
       , name='useflag_details_url'
    ),
    #}}}

    # Apps: #{{{
    url( r'^apps/'
       , 'app_stats'
       , name='app_stats_url'
    ),
    #}}}

    # TODO: /package/

    # API: #{{{
    url( r'^api', include(api.urls)),
    #}}}
)
