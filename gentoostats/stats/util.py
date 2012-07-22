from .models import UseFlag

def add_hyphens_to_uuid(uuid):
    """
    Try adding 4 hyphens to an UUID if its length after all existing hyphens are
    removed is 32. If that's not the case return the original UUID.

    UUID format: 8-4-4-4-12 groups of hex.
    """

    uuid_copy = uuid.replace('-', '')
    if len(uuid_copy) == 32:
        uuid = "%s-%s-%s-%s-%s" % ( uuid_copy[:8]
                                  , uuid_copy[8:12]
                                  , uuid_copy[12:16]
                                  , uuid_copy[16:20]
                                  , uuid_copy[20:]
        )

    return uuid

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

def get_useflag_objects(useflag_list):
    if not useflag_list:
        return useflag_list

    useflag_list = [
        UseFlag.objects.get_or_create(name=u)[0] \
        for u in useflag_list
    ]

    map(validate_item, useflag_list)

    return useflag_list
