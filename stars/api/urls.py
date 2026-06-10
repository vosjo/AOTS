from django.urls import include, path
from rest_framework import routers

from .plots import star_dataset_plots, star_sed_plot
from .star_detail import star_detail_bootstrap, star_parameters_overview
from .star_mutations import (
    bulk_upload_stars,
    create_star_from_form,
    resolve_simbad,
    star_editable_parameters,
    star_fetch_photometry_vizier,
    star_photometry_options,
    star_update_parameters,
    star_update_photometry,
)
from .views import (
    StarViewSet,  # star_remove_tag, star_add_tag,
    TagViewSet,
    IdentifierViewSet,
    getStarSpecfiles,
)

###from django.urls import include, re_path

app_name = 'stars-api'

router = routers.DefaultRouter()
router.register(r'stars', StarViewSet)
router.register(r'tags', TagViewSet)
router.register(r'identifiers', IdentifierViewSet, basename='identifier')

urlpatterns = [
    # Static star paths must come before the router (otherwise e.g. resolve-simbad
    # is captured as stars/<pk>/).
    path('stars/resolve-simbad/', resolve_simbad, name='star-resolve-simbad'),
    path('stars/create-from-form/', create_star_from_form, name='star-create-from-form'),
    path('stars/bulk-upload/', bulk_upload_stars, name='star-bulk-upload'),
    path(
        'stars/<int:star_pk>/specfiles/',
        getStarSpecfiles,
        name='stars_specfiles',
    ),
    path('stars/<int:pk>/sed/', star_sed_plot, name='star-sed-plot'),
    path('stars/<int:pk>/dataset-plots/', star_dataset_plots, name='star-dataset-plots'),
    path('stars/<int:pk>/detail/', star_detail_bootstrap, name='star-detail-bootstrap'),
    path(
        'stars/<int:pk>/parameters/',
        star_parameters_overview,
        name='star-parameters-overview',
    ),
    path(
        'stars/<int:pk>/photometry/options/',
        star_photometry_options,
        name='star-photometry-options',
    ),
    path(
        'stars/<int:pk>/photometry/',
        star_update_photometry,
        name='star-update-photometry',
    ),
    path(
        'stars/<int:pk>/photometry/from-vizier/',
        star_fetch_photometry_vizier,
        name='star-fetch-photometry-vizier',
    ),
    path(
        'stars/<int:pk>/parameters/editable/',
        star_editable_parameters,
        name='star-editable-parameters',
    ),
    path(
        'stars/<int:pk>/parameters/edit/',
        star_update_parameters,
        name='star-update-parameters',
    ),
    path('', include(router.urls)),
]
