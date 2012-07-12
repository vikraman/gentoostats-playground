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
