from django.conf import settings
from django.shortcuts import redirect, render
from fullctl.django.decorators import load_instance, require_auth

from django_prefixctl.models.prefixctl import PREFIX_MONITOR_CLASSES

# Create your views here.


def make_env(request, **kwargs):
    org = kwargs.get("org")
    r = {"env": settings.RELEASE_ENV, "version": settings.PACKAGE_VERSION}
    r.update(**kwargs)

    prefix_monitor_types = []

    for tag, mon in PREFIX_MONITOR_CLASSES.items():
        if request.perms.check(
            f"{mon['cls'].Grainy.namespace()}.{org.permission_id}", "r"
        ):
            prefix_monitor_types.append({"title": mon["title"], "tag": tag})

    r.update(PREFIX_MONITOR_CLASSES=prefix_monitor_types)
    r.update(MULTIPLE_PREFIX_MONITOR_CLASSES=(len(prefix_monitor_types) > 1))

    return r


@require_auth()
@load_instance()
def view_instance(request, instance, **kwargs):
    env = make_env(request, instance=instance, org=instance.org)
    return render(request, "theme-select.html", env)


@require_auth()
def org_redirect(request):
    return redirect(f"/{request.org.slug}/")
