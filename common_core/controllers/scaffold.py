from django.middleware.csrf import get_token, _unmask_cipher_token
from django.conf import settings


class ControllerScaffold:
    context = {
        "page_title": ""
    }

    app = ""
    submodule = ""
    tpl_base = ""
    tpl_node = ""

    def get_context_scaffold(self, request=None, *args, **kwargs):
        try:
            if self.force_csrf_to_context:
                self.context["csrf_token"] = _unmask_cipher_token(get_token(self.request))
        except AttributeError:
            pass

        self.context["base_url"] = settings.BASE_URL
        self.context["site_url"] = settings.SITE_URL

        if self.tpl_node:
            self.context["tpl_base"] = self.tpl_base
            self.context["tpl_node"] = self.tpl_node
            tpl_slug = self.tpl_node.split("/")[-1]
            self.context["tpl"] = f"{self.tpl_node}/{tpl_slug}.html"
            self.context["tpl_js"] = f"{self.tpl_node}/assets/{tpl_slug}.js.html"
            self.context["tpl_css"] = f"{self.tpl_node}/assets/{tpl_slug}.css.html"
            page_title = tpl_slug.replace("-", " ").replace("_", " ").title()
            self.context["page_title"] = f"- {page_title}"
        return self.context
