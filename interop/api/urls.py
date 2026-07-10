from django.urls import path

from . import views

app_name = 'interop-api'

urlpatterns = [
    path('astra/import/', views.astra_import_api, name='astra-import'),
    path('astra/import/<str:task_id>/', views.astra_import_status_api, name='astra-import-status'),
    path('astra/import/<str:task_id>/result/', views.astra_import_result_api, name='astra-import-result'),
    path('astra/export/', views.astra_export_api, name='astra-export'),
    path('astra/export/<str:task_id>/file/', views.astra_export_file_api, name='astra-export-file'),
]
