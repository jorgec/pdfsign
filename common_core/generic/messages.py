def explode_messages(messages: any, css_class: str = "bg-danger", wrapper_css_class: str = "", item_css_class: str = "text-danger-100"):
    if isinstance(messages, str):
        return f"<div class='{css_class} my-8 p-4'>{messages}</div>"
    try:
        __messages = f"<div class='{css_class} my-8 p-4'><ul class='{wrapper_css_class}'>"
        for m in messages:
            __messages += f"<li class='{item_css_class} my-2'>{m}</li>"
        __messages += "</ul></div>"
        return __messages
    except Exception:
        return ''
