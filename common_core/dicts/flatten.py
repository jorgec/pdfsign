def flatten_dict(d: dict, keep_parent: bool = True, parent_key: str = '', separator: str = ''):
    items = []
    for k, v in d.items():
        if keep_parent:
            new_key = f"{parent_key}{separator}{k}" if parent_key else k
        else:
            new_key = f"{k}"
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, separator=separator).items())
        else:
            items.append((new_key, v))
    return dict(items)


def flatten_querydict(query_dict):
    return {key: value[0] if len(value) == 1 else value for key, value in query_dict.lists()}
