from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from gentoostats.stats.models import *

def index(request):
    return HttpResponse("Hello, world.")

def hostdetails(request, host_id):
    host = get_object_or_404(Host, uuid=host_id)
    return render_to_response('stats/hostdetail.html', {'host_id': host_id})
