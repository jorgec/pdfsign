def slugify_uuid(uuid: str):
    try:
        return uuid.replace("-", "_")
    except AttributeError:
        return str(uuid).replace("-", "_")


def revert_slugged_uuid(uuid: str):
    try:
        return uuid.replace("_", "-")
    except AttributeError:
        return str(uuid).replace("_", "-")
