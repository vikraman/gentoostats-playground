from django import forms

from .models import *
from .util import add_hyphens_to_uuid

class HostSearchForm(forms.Form):
    host_id = forms.CharField(label='UUID')

    def clean_host_id(self):
        host_id = self.cleaned_data['host_id']
        host_id = add_hyphens_to_uuid(host_id).lower()

        if not Host.objects.filter(id=host_id).exists():
            raise forms.ValidationError("Invalid/Non-existent UUID.")

        return host_id
