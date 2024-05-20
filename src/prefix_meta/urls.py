from django.urls import path

import prefix_meta.views as views

urlpatterns = [
    path(
        "<str:org_tag>/export/meta/prefix/location/<str:ip>/<str:masklen>",
        views.export_locations,
        name="location-export",
    )
]
