from django.urls import path, include
from .views import StudentRegisterView,  CourseViewSet , ClassSessionViewSet, FingerprintAttendanceView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'sessions', ClassSessionViewSet, basename='session')


urlpatterns = [
    path('register/', StudentRegisterView.as_view(), name='student-register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('fingerprint/upload/', FingerprintUploadView.as_view(), name='fingerprint-upload'),
    path('attendance/scan/', FingerprintAttendanceView.as_view(), name='attendance-scan'),
    path('', include(router.urls)),
]
