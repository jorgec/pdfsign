from typing import Dict


def compare(old: Dict, new: Dict) -> Dict:
    common_keys = {}
    deleted_keys = {}
    new_keys = {}

    for key, val in old.items():
        if key in new:
            if val != new[key]:
                common_keys[key] = f"{key} changed from {val} to {new[key]}"
        else:
            deleted_keys[key] = f"{key} with value {val} removed"

    for key, val in new.items():
        if key not in old:
            new_keys[key] = f"New item {key} initialized with {val}"

    return {
        'has_changed': True,
        'changes': {
            'updated': common_keys,
            'deleted': deleted_keys,
            'created': new_keys
        }
    }
