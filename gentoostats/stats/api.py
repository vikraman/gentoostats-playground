from django.contrib.auth.models import User
from tastypie.resources import ModelResource
from tastypie import fields

from .models import *

class SubmissionResource(ModelResource):
    class Meta:
        queryset = Submission.objects.all()
        fields = ['id', 'host', 'protocol', 'arch', 'chost', 'cbuild',
                'ctarget', 'platform', 'profile', 'lang', 'lastsync',
                'makeconf', 'cflags', 'cxxflags', 'ldflags', 'fflags',
                'features', 'sync', 'mirrors', 'global_use', 'global_keywords',
                'makeopts', 'emergeopts', 'syncopts', 'acceptlicense']

        allowed_methods = ['get']
        include_absolute_url = True

class HostResource(ModelResource):
    latest_submission = \
        fields.ToOneField(SubmissionResource, 'latest_submission')

    class Meta:
        queryset = Host.objects.all()
        fields = ['id', 'added_on', 'latest_submission']

        allowed_methods = ['get']
        include_absolute_url = True
