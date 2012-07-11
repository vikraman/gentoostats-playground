import os
import json
import time
import pickle
import random
import logging
from datetime import datetime

from portage.dep import Atom as PortageAtom
from portage.exception import InvalidAtom
from portage._sets import SETPREFIX as SET_PREFIX

from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from gentoostats.stats.models import *

logger = logging.getLogger(__name__)

PROJECT_DIR = os.path.dirname(__file__)
CURRENT_PROTOCOL_VERSION = 2

class FileExistsException(Exception): pass
class BadRequestException(Exception): pass

# This should be defined at the module level:
class SimpleHttpRequest(object):
    def __init__(self, request):
        self.body = request.body
        self.META = filter( lambda x: isinstance(x[1], basestring)
                          , request.META.items()
        )

def save_request(request):
    """
    Saves all 'str' or 'unicode' properties of a Django Request object in a
    file.

    Returns the name of the newly created file.

    Throws FileExistsException if a new file could not be created.
    """

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

    return file_name

def validate_item(item):
    """
    Call .full_clean() on a Django model object.

    If this results in a ValidationError, then a BadRequestException is raised.
    """

    # TODO: also log information such as type(item).

    try:
        item.full_clean()
    except ValidationError as e:
        error_message = "Error: '%s' failed validation." % str(item)
        logger.info("validate_item(): " + error_message, exc_info=True)
        raise BadRequestException(error_message)

@csrf_exempt
@transaction.commit_on_success
def process_submission(request):
    """
    Saves and parses a stats submission.
    """

    # Before continuing let's save the whole request (for debugging):
    try:
        raw_request_filename = save_request(request)
    except FileExistsException as e:
        raise BadRequestException("Error: Unable to save your request.")

    # Parse the request:
    try:
        data = json.loads(request.body)
    except Exception as e:
        error_message = "Error: Unable to parse JSON data."
        logger.warning("process_submission(): " + error_message, exc_info=True)
        raise BadRequestException(error_message)

    # Check for AUTH data:
    try:
        # Make UUIDs case-insensitive by always using lower().
        uuid       = data['AUTH']['UUID'].lower()
        upload_key = data['AUTH']['PASSWD']
    except KeyError as e:
        error_message = "Error: Incomplete AUTH data."
        logger.info("process_submission(): " + error_message, exc_info=True)
        raise BadRequestException(error_message)

    try:
        protocol = data['PROTOCOL']
        assert type(protocol) == int
    except KeyError as e:
        error_message = "Error: No protocol specified."
        logger.info("process_submission(): " + error_message, exc_info=True)
        raise BadRequestException(error_message)
    except AssertionError as e:
        error_message = "Error: PROTOCOL must be an integer."
        logger.info("process_submission(): " + error_message, exc_info=True)
        raise BadRequestException(error_message)

    if protocol != CURRENT_PROTOCOL_VERSION:
        logger.info(
            "process_submission(): Unsupported protocol: %s." % (protocol),
            exc_info=True
        )

        raise BadRequestException(
            "Error: Unsupported protocol " + \
            "(only version %d is supported). " % CURRENT_PROTOCOL_VERSION + \
            "Please update your client."
        )

    lastsync = data.get('LASTSYNC')
    if lastsync:
        try:
            # FIXME: I've hardcoded the time zone here.
            # This is why: http://bugs.python.org/issue6641 .
            lastsync = datetime.fromtimestamp(time.mktime(
                time.strptime(lastsync, "%a, %d %b %Y %H:%M:%S +0000")
            ))
        except ValueError as e:
            error_message = "Error: Invalid date in LASTSYNC."
            logger.info("process_submission(): " + error_message, exc_info=True)
            raise BadRequestException(error_message)

    try:
        host, _ = Host.objects.get_or_create(id=uuid, upload_key=upload_key)
        host.full_clean()
    except IntegrityError as e:
        error_message = "Error: Invalid password."
        logger.info("process_submission(): " + error_message, exc_info=True)
        raise BadRequestException(error_message)
    except ValidationError as e:
        error_message = "Error: Invalid AUTH values."
        logger.info("process_submission(): " + error_message, exc_info=True)
        raise BadRequestException(error_message + " Is your password too long?")

    # AFAIK using bulk_create here is not worth it.

    features = data.get('FEATURES')
    if features:
        features = [
            Feature.objects.get_or_create(name=f)[0] for f in features
        ]

        map(validate_item, features)

    useflags = data.get('USE')
    if useflags:
        useflags = [
            UseFlag.objects.get_or_create(name=u)[0] for u in useflags
        ]

        map(validate_item, useflags)

    keywords = data.get('ACCEPT_KEYWORDS')
    if keywords:
        keywords = [
            Keyword.objects.get_or_create(name=k)[0] for k in keywords
        ]

        map(validate_item, keywords)

    mirrors = data.get('GENTOO_MIRRORS')
    if mirrors:
        mirrors = [
            MirrorServer.objects.get_or_create(url=m)[0] for m in mirrors
        ]

        map(validate_item, mirrors)

    lang = data.get('LANG')
    if lang:
        lang, _ = Lang.objects.get_or_create(name=lang)
        validate_item(lang)

    sync = data.get('SYNC')
    if sync:
        sync, _ = SyncServer.objects.get_or_create(url=sync)
        validate_item(sync)

    submission = Submission.objects.create(
        raw_request_filename = raw_request_filename,

        host          = host,
        email         = data['AUTH'].get('EMAIL'),
        ip_addr       = request.META['REMOTE_ADDR'],
        fwd_addr      = request.META.get('HTTP_X_FORWARDED_FOR'), # TODO

        protocol      = protocol,

        arch          = data.get('ARCH'),
        chost         = data.get('CHOST'),
        cbuild        = data.get('CBUILD'),
        ctarget       = data.get('CTARGET'),

        platform      = data.get('PLATFORM'),
        profile       = data.get('PROFILE'),
        makeconf      = data.get('MAKECONF'),

        cflags        = data.get('CFLAGS'),
        cxxflags      = data.get('CXXFLAGS'),
        ldflags       = data.get('LDFLAGS'),
        cppflags      = data.get('CPPFLAGS'),
        fflags        = data.get('FFLAGS'),

        makeopts      = data.get('MAKEOPTS'),
        emergeopts    = data.get('EMERGE_DEFAULT_OPTS'),
        syncopts      = data.get('PORTAGE_RSYNC_EXTRA_OPTS'),
        acceptlicense = data.get('ACCEPT_LICENSE'),

        lang          = lang,
        sync          = sync,

        lastsync      = lastsync,
    )

    submission.features.add(*features)
    submission.mirrors.add(*mirrors)

    submission.global_use.add(*useflags)
    submission.global_keywords.add(*keywords)

    packages = data.get('PACKAGES')
    if packages:
        for package, info in packages.items():
            try:
                atom = PortageAtom( "=" + package
                                  , allow_wildcard = False
                                  , allow_repo     = True
                )
                assert atom.blocker == False and atom.operator == '='

                category, package_name = atom.cp.split('/')

                category, _ = Category.objects.get_or_create(name=category)
                category.full_clean()

                package_name, _ = PackageName.objects.get_or_create(name=package_name)
                package_name.full_clean()

                package, _ = Package.objects.get_or_create(
                    category     = category,
                    package_name = package_name,

                    version      = atom.cpv.lstrip(atom.cp),
                    slot         = atom.slot,
                    repository   = atom.repo,
                )
                package.full_clean()

            except (InvalidAtom, ValidationError) as e:
                error_message = "Error: Atom '%s' failed validation." % package
                logger.info("process_submission(): " + error_message, exc_info=True)
                raise BadRequestException(error_message)

            keyword = info.get('KEYWORD')
            if keyword:
                keyword, _ = Keyword.objects.get_or_create(name=keyword)
                keyword.full_clean()

            built_at = info.get('BUILD_TIME')
            if not built_at:
                # Sometimes clients report BUILD_TIME as ''.
                built_at = None
            else:
                built_at = datetime.fromtimestamp(float(built_at))

            build_duration = info.get('BUILD_DURATION')
            if not build_duration:
                build_duration = None

            size = info.get('SIZE')
            if not size:
                size = None

            installation, _ = Installation.objects.get_or_create(
                package    = package,
                submission = submission,
                keyword    = keyword,

                built_at       = built_at,
                build_duration = build_duration, # TODO
                size           = size,
            )

            def _get_useflag_objects(useflag_list):
                if not useflag_list:
                    return useflag_list

                useflag_list = [
                    UseFlag.objects.get_or_create(name=u)[0] \
                    for u in useflag_list
                ]

                map(validate_item, useflag_list)

                return useflag_list

            iuse   = _get_useflag_objects(info.get('IUSE'))
            pkguse = _get_useflag_objects(info.get('PKGUSE'))
            use    = _get_useflag_objects(info.get('USE'))

            if iuse:
                installation.iuse.add(*iuse)
            if pkguse:
                installation.pkguse.add(*pkguse)
            if use:
                installation.use.add(*use)

            installation.full_clean()

    reported_sets = data.get('WORLDSET')
    if reported_sets:
        for set_name, entries in reported_sets.items():
            try:
                atom_set, _ = AtomSet.objects.get_or_create(
                    name  = set_name,
                    owner = submission,
                )

                for entry in entries:
                    try:
                        if entry.startswith(SET_PREFIX):
                            subset_name = entry[len(SET_PREFIX):]

                            subset, _ = AtomSet.objects.get_or_create(
                                name  = subset_name,
                                owner = submission,
                            )
                            subset.full_clean()

                            atom_set.subsets.add(subset)
                        else:
                            patom = PortageAtom( entry
                                               , allow_wildcard = False
                                               , allow_repo     = True
                            )

                            category, package_name = patom.cp.split('/')

                            category, _ = Category.objects.get_or_create(name=category)
                            category.full_clean()

                            package_name, _ = PackageName.objects.get_or_create(name=package_name)
                            package_name.full_clean()

                            atom, _ = Atom.objects.get_or_create(
                                full_atom    = entry,
                                operator     = patom.operator or '',

                                category     = category,
                                package_name = package_name,
                                version      = patom.cpv.lstrip(patom.cp),
                                slot         = patom.slot,
                                repository   = patom.repo,
                            )

                            atom.full_clean()
                            atom_set.atoms.add(atom)
                    except (InvalidAtom, ValidationError) as e:
                        error_message = "Error: Atom/set '%s' failed validation." % entry
                        logger.info("process_submission(): " + error_message, exc_info=True)
                        raise BadRequestException(error_message)

                atom_set.full_clean()
                submission.reported_sets.add(atom_set)
            except ValidationError as e:
                error_message = \
                        "Error: Selected set '%s' failed validation." \
                        % selectedset

                logger.info("process_submission(): " + error_message, exc_info=True)
                raise BadRequestException(error_message)

    submission.full_clean()
    return HttpResponse("Success")

@csrf_exempt
@require_POST
def accept_submission(request):
    """
    Simple wrapper around process_submission().
    """

    try:
        return process_submission(request)
    except BadRequestException as e:
        return HttpResponseBadRequest(str(e))
    except Exception as e:
        logger.error("process_submission(): " + str(e), exc_info=True)
        return HttpResponseBadRequest(
            "Error: something went wrong. The administrator has been " + \
            "notified and will look into the problem."
        )
