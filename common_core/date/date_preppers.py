import arrow


def human_readable_date(d: str):

    try:
        prepped = arrow.get(d).humanize()
    except arrow.ParserError:
        prepped = arrow.get(prep_for_isodate(d)).humanize()

    return prepped


def prep_for_isodate(d: str):
    if not isinstance(d, str):
        raise TypeError("String required")

    try:
        prepped_date = arrow.get(d).format("YYYY-MM-DD")
    except arrow.ParserError:
        if "/" in d:
            __d = d.split("/")
            if len(__d[2]) == 4:
                preprep_date = f"{__d[2]}-{__d[1]}-{__d[0]}"
            elif len(__d[0]) == 4:
                preprep_date = f"{__d[0]}-{__d[1]}-{__d[2]}"
            else:
                raise ValueError(f"Invalid date format: {d}")

            try:
                prepped_date = arrow.get(preprep_date).format("YYYY-MM-DD")
            except arrow.ParserError:
                raise ValueError(f"Invalid date format: {d}")
        else:
            raise ValueError(f"Invalid date format: {d}")

    return prepped_date.format("YYYY-MM-DD")
