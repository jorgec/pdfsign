from typing import Dict

from django.db.models import ForeignKey


def filtered_queryset(model, params: Dict):
    fields = []
    for field in model._meta.fields:
        fields.append(field.name)
        if isinstance(field, ForeignKey):
            fields.append(field.name + "_id")

    filters = {}

    for param, val in params.items():
        if val:
            if "__" in param:
                filters[param] = val
            else:
                if param in fields:
                    filters[param] = val
                else:
                    if "_start" in param:
                        __param = param.replace("_start", "")
                        if __param in fields:
                            filters[__param + "__gte"] = val
                    if "_end" in param:
                        __param = param.replace("_end", "")
                        if __param in fields:
                            filters[__param + "__lte"] = val



    return model.objects.filter(**filters)
