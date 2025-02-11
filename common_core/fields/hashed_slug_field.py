from django_extensions.db.fields import AutoSlugField
from django.utils.encoding import force_str

from common_core.generic.random_string import generate_random_string


class HashedAutoSlugField(AutoSlugField):
    def create_slug(self, model_instance, add):
        slug = super().create_slug(model_instance, add)
        slug = slug.replace("-", "_")
        return f"{slug}___{generate_random_string(16)}"

    def pre_save(self, model_instance, add):
        if not model_instance.slug:
            value = force_str(self.create_slug(model_instance, add))
            return value
        return model_instance.slug
