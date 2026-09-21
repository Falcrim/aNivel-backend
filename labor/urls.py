from django.urls import path, include

urlpatterns = [
    path('', include('labor.api.urls')),
]
