from typing import Dict


def instance_update(instance, data: Dict):
    instance_pk = instance.pk
    for key, value in data.items():
        if hasattr(instance, key):
            if value == "None" or value == "" or not value:
                value = None
            setattr(instance, key, value)
        else:
            pass
    instance.save(force_update=True)
    return instance.__class__.objects.get(pk=instance_pk)
