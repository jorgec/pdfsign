from django.http import HttpResponse


def process_breaks(res):
    if res["code"] == 403:
        return HttpResponse('401 Forbidden', status=403)
