import os
import json
import time
import pickle
import random
import logging
from datetime import datetime

from portage.dep import Atom

from django.http import HttpResponse, HttpResponseBadRequest
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from gentoostats.stats.models import *

logger = logging.getLogger(__name__)

PROJECT_DIR = os.path.dirname(__file__)
CURRENT_PROTOCOL_VERSION = 2

class FileExistsException(Exception): pass

# This should be defined at the module level:
class SimpleHttpRequest(object):
    def __init__(self, request):
        self.body = request.body
        self.META = filter(lambda x: isinstance(x[1], basestring), request.META.items())

def save_request(request):
    ip_addr = request.META['REMOTE_ADDR']

    # We can't serialise the whole object, so we only serialise the strings:
    request_copy = SimpleHttpRequest(request)

    # current unix timestamp, without microseconds:
    timestamp = str(int(time.time()))

    # append a random int, just for safety
    random_int = random.randint(1, 1024)

    file_name = "%s-%s-%s" % (ip_addr, timestamp, random_int)
    file_path = os.path.join(PROJECT_DIR, 'requests', file_name)

    if os.path.exists(file_path):
        error_message = "File '%s' already exists" % (file_path)

        logger.error("save_request(): %s" % (error_message))
        raise FileExistsException(error_message)

    with open(file_path, 'wb') as f:
        pickle.dump(request_copy, f)

# @transaction.commit_on_success
@csrf_exempt
def process_submission(request):
    if request.method != 'POST':
        logger.info("process_submission(): Invalid method use attempt.")
        return HttpResponseBadRequest("Error: You are not using POST.")

    # Before continuing let's save the whole request (for debugging):
    try:
        save_request(request)
    except FileExistsException as e:
        return HttpResponseBadRequest(
            "Error: You are sending too many requests."
        )
    except:
        raise

    # Parse the request:
    try:
        data = json.loads(request.body)
    except Exception as e:
        logger.warning("process_submission(): Failed parsing JSON.", exc_info=True)
        return HttpResponseBadRequest("Error: Malformed JSON data.")

    # Check for AUTH data:
    try:
        uuid       = data['AUTH']['UUID']
        upload_key = data['AUTH']['PASSWD']
    except Exception as e:
        logger.info("process_submission(): No AUTH data.", exc_info=True)
        return HttpResponseBadRequest("Error: AUTH data is missing.")

    try:
        protocol = data['PROTOCOL']
    except Exception as e:
        logger.info("process_submission(): Error parsing protocol.", exc_info=True)
        return HttpResponseBadRequest("Error: Unable to parse PROTOCOL.")

    if protocol != CURRENT_PROTOCOL_VERSION:
        logger.info(
            "process_submission(): Unsupported protocol: %s" % (protocol),
            exc_info=True
        )

        return HttpResponseBadRequest(
            "Error: Unsupported protocol. Please update your client."
        )


    host = Host(id=uuid, upload_key=upload_key)
    try:
        host.clean_fields()
    except:
        logger.info("process_submission(): Invalid AUTH values.", exc_info=True)
        return HttpResponseBadRequest("Error: Invalid AUTH values.")

    with transaction.commit_manually():
        try:
            # This is going to error out if the upload_key is different.
            host, created = Host.objects.get_or_create(id=uuid, upload_key=upload_key)
        except IntegrityError as e:
            logger.info("process_submission(): Invalid password.", exc_info=True)
            return HttpResponseBadRequest("Error: invalid password.")

        try:
            lastsync = data.get('LASTSYNC', None)
            if lastsync:
                lastsync = datetime.fromtimestamp(time.mktime(
                    time.strptime(lastsync, "%a, %d %b %Y %H:%M:%S +0000")
                ))

            submission = Submission.objects.create(
                host     = host,
                email    = data['AUTH'].get('EMAIL', ''),
                ip_addr  = request.META['REMOTE_ADDR'],
                fwd_addr = request.META.get('REMOTE_ADDR', None),

                protocol = int(data['PROTOCOL']),

                arch     = data.get('REMOTE_ADDR', ''),
                chost    = data.get('CHOST',       ''),
                cbuild   = data.get('CBUILD',      ''),
                ctarget  = data.get('CTARGET',     ''),

                platform = data.get('PLATFORM',    ''),
                profile  = data.get('PROFILE',     ''),
                # lang     = TODO
                lastsync = lastsync,
                makeconf = data.get('MAKECONF',    ''),

                cflags   = data.get('CFLAGS',      ''),
                cxxflags = data.get('CXXFLAGS',    ''),
                ldflags  = data.get('LDFLAGS',     ''),
                cppflags = data.get('CPPFLAGS',    ''),
                fflags   = data.get('FFLAGS',      ''),

                # features = TODO
                # sync     = TODO
                # mirrors  = TODO

                # global_use      = TODO
                # global_keywords = TODO

                # installed_packages = TODO
                # selected_atoms     = TODO

                # makeopts      = TODO
                # emergeopts    = TODO
                # syncopts      = TODO
                # acceptlicense = TODO
            )

            transaction.commit()
            return HttpResponse("Success")

        except Exception as e:
            transaction.rollback()

            logger.error("process_submission(): Pre-transaction failure.", exc_info=True)
            return HttpResponseBadRequest("Error: something went wrong.")
        else:
            # This never actually gets executed.
            transaction.commit()
