from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin


from .models import User



class CustomUserAdmin(UserAdmin):
   
   model = User
   
   list_display = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_student', 'is_projectmanager', 'is_superuser']
   
   fieldsets = (
               (None, {'fields': ('username', 'email', 'password')}),
               ('Permissions', {'fields': ('is_superuser', 'is_staff', 'is_active', 'is_student', 'is_projectmanager')}),
   )
   
admin.site.register(User, CustomUserAdmin,)
