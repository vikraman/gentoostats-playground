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

    url( r'^faq/$'
       , 'faq'
       , name='faq_url'
    ),

    url( r'^about/$'
       , 'about'
       , name='about_url'
    ),

    url( r'^stats/$'
       , 'stats'
       , name='stats_url'
    ),

    url( r'^stats/overall/$'
       , 'overall_stats'
       , name='overall_stats_url'
    ),

    # Host(s): #{{{
    url( r'^stats/host/$'
       , 'host_search'
       , name='host_search_url'
    ),

    url( r'^stats/(?:host/)(?P<host_id>[\da-fA-F]{8}-?[\da-fA-F]{4}-?[\da-fA-F]{4}-?[\da-fA-F]{4}-?[\da-fA-F]{12})/$'
       , 'host_details'
       , name='host_details_url'
    ),
    #}}}

    # ARCH(es): #{{{
    url( r'^stats/arch/(?P<arch>\w+)/'
       , 'arch_details'
       , name='arch_details_url'
    ),
    #}}}

    # FEATURE(s): #{{{
    url( r'^stats/feature/(?P<feature>\S+)/'
       , 'feature_details'
       , name='feature_details_url'
    ),
    #}}}

    # Keyword(s): #{{{
    url( r'^stats/keyword/(?P<keyword>\w+)/'
       , 'keyword_details'
       , name='keyword_details_url'
    ),
    #}}}

    # Repository(ies): #{{{
    url( r'^stats/repository/$'
       , 'repository_stats'
       , name='repository_stats_url'
    ),

    url( r'^stats/repository/(?P<repository>\S+)/'
       , 'repository_details'
       , name='repository_details_url'
    ),
    #}}}

    # Servers: #{{{
    url( r'^stats/servers/$'
       , 'server_stats'
       , name='server_stats_url'
    ),

    url( r'^stats/servers/mirror/(?P<server_id>\S+)/'
       , 'mirror_details'
       , name='mirror_details_url'
    ),

    url( r'^stats/servers/sync/(?P<server_id>\S+)/'
       , 'sync_details'
       , name='sync_details_url'
    ),
    #}}}

    # Profile(s): #{{{
    url( r'^stats/profile/(?P<profile>\S+)/'
       , 'profile_details'
       , name='profile_details_url'
    ),
    #}}}

    # LANG(s): #{{{
    url( r'^stats/lang/(?P<lang>\S+)/'
       , 'lang_details'
       , name='lang_details_url'
    ),
    #}}}

    # Category(ies): #{{{
    url( r'^stats/category/$'
       , 'category_stats'
       , name='category_stats_url'
    ),

    url( r'^stats/category/(?P<category>\S+)/'
       , 'category_details'
       , name='category_details_url'
    ),
    #}}}

    # Submission(s): #{{{
    url( r'^stats/submission/(?P<id>\d+)/'
       , 'submission_details'
       , name='submission_details_url'
    ),
    #}}}

    # USE flag(s): #{{{
    url( r'^stats/use/$'
       , 'useflag_stats'
       , name='useflag_stats_url'
    ),

    url( r'^stats/use/(?P<useflag>\S+)/'
       , 'useflag_details'
       , name='useflag_details_url'
    ),
    #}}}

    # Apps: #{{{
    url( r'^stats/apps/'
       , 'app_stats'
       , name='app_stats_url'
    ),
    #}}}

    # TODO: /package/

    # API: #{{{
    # url( r'^api', include(api.urls)),
    #}}}
)
