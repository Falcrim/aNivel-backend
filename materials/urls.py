from django.urls import path, include

app_name = 'materials'

urlpatterns = [
    path('', include('materials.api.urls')),
]
