import os
import time
import pickle
import random
import logging

PROJECT_DIR = os.path.dirname(__file__)

logger = logging.getLogger(__name__)

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
