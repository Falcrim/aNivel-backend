from django.contrib import admin

# Register your models here.
from .models import Project, Category, Subcategory

admin.site.register(Project)
admin.site.register(Category)
admin.site.register(Subcategory)