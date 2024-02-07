from rest_framework import routers

router = routers.DefaultRouter()


def route(viewset):
    if hasattr(viewset, "ref_tag"):
        ref_tag = viewset.ref_tag
    else:
        ref_tag = viewset.serializer_class.ref_tag

    if getattr(viewset, "ix_tag_needed", None):
        prefix = f"{ref_tag}/(?P<org_tag>[^/]+)/(?P<ix_tag>[^/]+)"
    else:
        prefix = f"{ref_tag}/(?P<org_tag>[^/]+)"

    router.register(prefix, viewset, basename=ref_tag)
    return viewset
