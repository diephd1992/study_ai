from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VideoRequestViewSet

# Router để tự động tạo URLs
router = DefaultRouter()
router.register(r'videos', VideoRequestViewSet, basename='video')

urlpatterns = [
    path('api/', include(router.urls)),
]
