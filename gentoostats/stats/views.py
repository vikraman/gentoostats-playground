from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from gentoostats.stats.models import *

def index(request):
    return HttpResponse("Hello, world.")

def host_details(request, host_id):
    host = get_object_or_404(Host, id=host_id)

    submission_history = \
        host.submissions.all().order_by('datetime').values_list('datetime', 'protocol')

    latest_submission = list(host.submissions.all().order_by('-datetime')[:1])
    if latest_submission:
        latest_submission = latest_submission[0]
    else:
        latest_submission = None

    context = {
        'host':               host,
        'latest_submission':  latest_submission,
        'submission_history': submission_history,
    }

    if latest_submission:
        context['tree_age'] = int(
            (latest_submission.datetime - latest_submission.lastsync).total_seconds()
        )

    return render_to_response('stats/host_details.html', context)
