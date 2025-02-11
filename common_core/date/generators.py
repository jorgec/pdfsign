import pytz
from datetime import datetime

import arrow
from django.conf import settings


def dt_now(to_string: bool = False, human_readable: str = None, split: str = None):
    t = datetime.now(pytz.timezone(settings.TIME_ZONE))

    if human_readable:
        hr = arrow.get(t).format(human_readable)
        if split:
            hr = hr.split(split)
        t = hr

    if to_string:
        return f"{t}"
    return t
