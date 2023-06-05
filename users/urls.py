from django.urls import path
from . import views

app_name = 'users'
urlpatterns = [
    path('you/', views.thisUsersPage, name='personal_page'),
    path('user/<int:user_id>', views.foreignUsersPage, name='foreigners_page'),
]
