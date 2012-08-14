from __future__ import division

import json
import operator
import datetime

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page, cache_control
from django.core.urlresolvers import reverse
from django.utils.timezone import utc
from django.views.generic import ListView, DetailView
from django.db.models import Q, Min, Max, Count
from django.shortcuts import render, redirect, \
                             get_object_or_404, get_list_or_404

from .util import split_list, add_hyphens_to_uuid
from .forms import *
from .models import *

FRESH_SUBMISSION_MAX_AGE = 30 # in days

class ImprovedDetailView(DetailView):
    """
    A DetailView subclass that respects 'extra_context'.
    """

    extra_context = dict()
    def get_context_data(self, **kwargs):
        context = super(ImprovedDetailView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

class ImprovedListView(ListView):
    """
    A ListView subclass that respects 'extra_context'.
    """

    extra_context = dict()
    def get_context_data(self, **kwargs):
        context = super(ImprovedListView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

@cache_control(public=True)
@cache_page(1 * 60)
def index(request):
    """
    Index page of Gentoostats.
    """

    return render(request, 'stats/index.html')

@cache_control(public=True)
@cache_page(24 * 60 * 60)
def faq(request):
    """
    F.A.Q page.
    """

    return render(request, 'stats/not_implemented.html')

@cache_control(public=True)
@cache_page(24 * 60 * 60)
def about(request):
    """
    Project about page.
    """

    return render(request, 'stats/about.html')

@cache_control(public=True)
@cache_page(24 * 60 * 60)
def stats(request):
    """
    Stats index page.
    """

    return render(request, 'stats/stats_index.html')

@cache_control(public=True)
@cache_page(1 * 60)
def overall_stats(request):
    """
    Show overall stats for the website.
    """

    latest_submission_q = Q(submissions__in=Submission.objects.latest_submission_ids)

    features = Feature.objects.filter(latest_submission_q).annotate(num_hosts_fast=Count('submissions')).order_by('name')
    langs    = Lang.objects.filter(latest_submission_q).annotate(num_hosts_fast=Count('submissions')).order_by('name')
    keywords = Keyword.objects.filter(latest_submission_q).annotate(num_hosts_fast=Count('submissions')).order_by('name')

    context = dict(
        hosts         = Host.objects.all(),
        submissions   = Submission.objects.select_related().order_by('-datetime'),
        country_stats = Submission.objects.latest_submissions.filter(country__isnull=False).values_list('country').annotate(num_hosts=Count('country')).order_by('country'),
        arch_stats    = Submission.objects.latest_submissions.values_list('arch').annotate(num_hosts=Count('arch')).order_by('arch'),
        profile_stats = Submission.objects.latest_submissions.values_list('profile').annotate(num_hosts=Count('profile')).order_by('profile'),

        features = features,
        langs    = langs,
        keywords = keywords,
    )

    return render(request, 'stats/overall_stats.html', context)

@cache_control(public=True)
@cache_page(24 * 60 * 60)
def host_search(request):
    """
    Search for a host by its full UUID.
    """

    if request.method == 'POST':
        form = HostSearchForm(request.POST)
        if form.is_valid():
            return redirect( 'stats:host_details_url'
                           , host_id   = form.cleaned_data['host_id']
                           , permanent = False
            )
    else:
        form = HostSearchForm(
            # initial = dict(host_id='Enter UUID'),
        )

    context = dict(
        form=form,
    )

    return render(request, 'stats/host_search.html', context)

@cache_control(private=True)
@cache_page(1 * 60)
def host_details(request, host_id):
    """
    Show statistics about a certain host.
    """

    # Accept UUIDs with no hyphens and/or with capital letters, but still
    # redirect the user to the 'proper' URL:
    host_id_new = add_hyphens_to_uuid(host_id)
    host_id_new = host_id_new.lower()

    if host_id != host_id_new:
        return redirect( 'stats:host_details_url'
                       , host_id   = host_id_new
                       , permanent = True
        )

    context = dict(
        host = get_object_or_404( Host.objects.select_related('submissions')
                                , id = host_id
        ),
    )

    return render(request, 'stats/host_details.html', context)

@cache_control(public=True)
@cache_page(1 * 60)
def arch_details(request, arch):
    """
    Show more detailed statistics about a specific arch.
    """

    context = dict(
        arch            = arch,
        num_submissions = Submission.objects.filter(arch=arch).count(),
        num_all_hosts   = Submission.objects.filter(arch=arch).order_by().aggregate(Count('host', distinct=True)).values()[0],
        num_hosts       = Submission.objects.latest_submissions.filter(arch=arch).count(),
    )

    return render(request, 'stats/arch_details.html', context)

@cache_control(public=True)
@cache_page(1 * 60)
def keyword_details(request, keyword):
    """
    Show statistics about a particular keyword (e.g. amd64).
    """

    context = dict(
        keyword = get_object_or_404(Keyword, name=keyword),
    )

    return render(request, 'stats/keyword_details.html', context)

@cache_control(public=True)
@cache_page(1 * 60)
def feature_details(request, feature):
    """
    Show statistics about a particular FEATURE.
    """

    context = dict(
        feature = get_object_or_404(Feature, name=feature),
    )

    return render(request, 'stats/feature_details.html', context)

@cache_control(public=True)
@cache_page(1 * 60)
def mirror_stats(request):
    """
    Show statistics about the known mirrors.
    """

    context = dict(
        mirrors = MirrorServer.objects.all()
    )

    return render(request, 'stats/mirror_stats.html', context)

@cache_control(public=True)
@cache_page(1 * 60)
def mirror_details(request, mirror):
    """
    Show more detailed statistics about a specific mirror.
    """

    context = dict(
        mirror = get_object_or_404(MirrorServer, url=mirror)
    )

    return render(request, 'stats/mirror_details.html', context)

@cache_control(public=True)
@cache_page(1 * 60)
def sync_stats(request):
    """
    TODO: add a description.
    """

    return render(request, 'stats/not_implemented.html')

@cache_control(public=True)
@cache_page(1 * 60)
def sync_details(request, sync):
    """
    TODO: add a description.
    """

    return render(request, 'stats/not_implemented.html')

@cache_control(public=True)
@cache_page(1 * 60)
def repository_stats(request):
    """
    TODO: add a description.
    """

    return render(request, 'stats/not_implemented.html')

@cache_control(public=True)
@cache_page(1 * 60)
def repository_details(request, repository):
    """
    TODO: add a description.
    """

    return render(request, 'stats/not_implemented.html')

@cache_control(public=True)
@cache_page(1 * 60)
def category_stats(request):
    """
    TODO: add a description.
    """

    return render(request, 'stats/not_implemented.html')

@cache_control(public=True)
@cache_page(1 * 60)
def category_details(request, category):
    """
    TODO: add a description.
    """

    return render(request, 'stats/not_implemented.html')

@cache_control(public=True)
@cache_page(1 * 60)
def lang_details(request, lang):
    """
    TODO: add a description.
    """

    return render(request, 'stats/not_implemented.html')

# Submissions: #{{{
class SubmissionDetailView(ImprovedDetailView):
    context_object_name = 'submission'
    queryset = Submission.objects.select_related()
    pk_url_kwarg = 'id'

submission_details = \
    cache_control(private=True) (
        cache_page(24 * 60 * 60) (
            SubmissionDetailView.as_view()
        )
    )
#}}}

@cache_control(public=True)
@cache_page(1 * 60)
def useflag_stats(request):
    """
    TODO: add a description.
    """

    return render(request, 'stats/not_implemented.html')

@cache_control(public=True)
@cache_page(1 * 60)
def useflag_details(request, useflag):
    """
    TODO: add a description.
    """

    return render(request, 'stats/not_implemented.html')

@cache_control(public=True)
@cache_page(1 * 60)
def profile_details(request, profile):
    """
    TODO: add a description.
    """

    return render(request, 'stats/not_implemented.html')

@cache_control(public=True)
@cache_page(0)
def app_stats(request, dead=False):
    stats = [
        [ 'Browsers'
        ,   ['Chrome', 'www-client/google-chrome', 'www-client/chromium']
        ,   ['Firefox', 'www-client/firefox', 'www-client/firefox-bin']
        ,   ['Opera', 'www-client/opera']
        ,   ['Epiphany', 'www-client/epiphany']
        ,   ['Konqueror', 'kde-base/konqueror']
        ,   ['rekonq', 'www-client/rekonq']
        ,   ['Conkeror', 'www-client/conkeror']
        ,   ['Midori', 'www-client/midori']
        ,   ['Uzbl', 'www-client/uzbl']
        ],

        [ 'CLI Browsers'
        ,   ['Wget', 'net-misc/wget']
        ,   ['cURL', 'net-misc/curl']
        ,   ['Lynx', 'www-client/lynx']
        ,   ['Links', 'www-client/links']
        ,   ['ELinks', 'www-client/elinks']
        ,   ['W3M', 'www-client/w3m', 'www-client/w3mmee']
        ],

        [ 'Editors/IDEs'
        ,   ['Vi/Vim', 'app-editors/vim', 'app-editors/gvim', 'app-editors/nvi', 'app-editors/elvis']
        ,   ['Emacs', 'app-editors/emacs', 'app-editors/qemacs', 'app-editors/xemacs', 'app-editors/jove']
        ,   ['Eclipse', 'dev-util/eclipse-sdk']
        ,   ['Yi', 'app-editors/yi']
        ,   ['Nano', 'app-editors/nano']
        ,   ['Gedit', 'app-editors/gedit']
        ,   ['Kate', 'kde-base/kate']
        ,   ['Kwrite', 'kde-base/kwrite']
        ,   ['Ne', 'app-editors/ne']
        ,   ['Jed', 'app-editors/jed']
        ,   ['Jedit', 'app-editors/jedit']
        ,   ['Joe', 'app-editors/joe']
        ,   ['Ed', 'sys-apps/ed']
        ,   ['Leafpad', 'app-editors/leafpad']
        ,   ['Geany', 'dev-util/geany']
        ],

        [ 'Desktop Environments'
        ,   ['KDE SC', 'kde-base/kdebase-meta']
        ,   ['GNOME', 'gnome-base/gnome']
        ,   ['Xfce', 'xfce-base/xfce4-meta']
        ,   ['LXDE', 'lxde-base/lxde-meta']
        #,   ['E17', 'dev-libs/ecore']
        ],

        [ 'Window Managers'
        ,   ['Xmonad', 'x11-wm/xmonad']
        ,   ['Ratpoison', 'x11-wm/ratpoison']
        ,   ['Openbox', 'x11-wm/openbox']
        ,   ['Fluxbox', 'x11-wm/fluxbox']
        ,   ['Enlightenment', 'x11-wm/enlightenment']
        ,   ['dwm', 'x11-wm/dwm']
        ,   ['i3', 'x11-wm/i3']
        ,   ['Compiz', 'x11-wm/compiz', 'x11-wm/compiz-fusion']
        ,   ['FVWM', 'x11-wm/fvwm']
        ,   ['Wmii', 'x11-wm/wmii']
        ,   ['Window Maker', 'x11-wm/windowmaker']
        ,   ['subtle', 'x11-wm/subtle']
        ,   ['awesome', 'x11-wm/awesome']
        ,   ['evilwm', 'x11-wm/evilwm']
        ,   ['IceWM', 'x11-wm/icewm']
        ],

        [ 'Shells'
        ,   ['Bash', 'app-shells/bash']
        ,   ['Zsh', 'app-shells/zsh']
        ,   ['Tcsh', 'app-shells/tcsh']
        ,   ['fish', 'app-shells/fish']
        ],

        [ 'Web servers'
        ,   ['Apache', 'www-servers/apache']
        ,   ['Nginx', 'www-servers/nginx']
        ,   ['lighttpd', 'www-servers/lighttpd']
        ],

        [ 'Graphics Drivers'
        ,   ['Nvidia (proprietary)', 'x11-drivers/nvidia-drivers']
        ,   ['Nouveau', 'x11-drivers/xf86-video-nouveau']
        ,   ['fglrx (proprietary)', 'x11-drivers/ati-drivers']
        ,   ['radeon', 'x11-drivers/xf86-video-ati']
        ,   ['Intel', 'x11-drivers/xf86-video-intel']
        ],
    ]

    delta = datetime.timedelta(days=FRESH_SUBMISSION_MAX_AGE)
    submission_age = datetime.datetime.utcnow().replace(tzinfo=utc) - delta

    fresh_submissions_qs = Submission.objects.latest_submissions.filter(datetime__gte=submission_age)
    num_hosts = fresh_submissions_qs.count()

    def percentify(n):
        # TODO: uncomment this in production.
        # return round(100 * n / num_hosts)

        import random
        return random.randint(0, 100)

    for section in stats:
        cat, apps = split_list(section)
        for app in apps:
            # Turn this: ['Vi/Vim', 'app-editors/vim', 'app-editors/gvim', ...]
            # into this: [('Vi/Vim', nT), ('app-editors/vim', n1), ('app-editors/gvim', n2), ...]
            # 'nT' is the total percentage of hosts with this app, calculated by
            # chaining Q objects. n1, n2, etc. are also percentages.

            q_list = []
            name, pkgs = split_list(app)

            for index, pkg in enumerate(pkgs):
                q_list.append(Q(installations__package__cp=pkg))

                num = fresh_submissions_qs.filter(installations__package__cp=pkg).count()
                app[index+1] = (pkg, percentify(num))

            num_total = fresh_submissions_qs.filter(reduce(operator.or_, q_list)).distinct().count()
            app[0] = (name, percentify(num_total))

        # sort 'apps' by each app's usage percentage:
        section[1:] = sorted(apps, key=lambda x: x[0][1], reverse=True)

    context = dict(
        num_hosts = num_hosts,
        dead      = dead,
        stats     = json.dumps(stats),
    )

    return render(request, 'stats/app_stats.html', context)
