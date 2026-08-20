from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, LoginView, HabitViewSet


appname = "api.apps.ApiConfig"

router = DefaultRouter()
router.register(r'habits', HabitViewSet, basename='habit')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('', include(router.urls)),
]
