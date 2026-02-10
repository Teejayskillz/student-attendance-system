from django.urls import path, include
from .views import StudentRegisterView, FingerprintAttendanceViewSet, CourseViewSet , ClassSessionViewSet, FingerprintAttendanceView , FingerprintUploadView, AdminAttendanceReportView, AdminAttendanceUpdateView, AdminUserListView,LecturerAttendanceDashboard, AdminAttendanceDashboard
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'sessions', ClassSessionViewSet, basename='session')
router.register(r'attendance', FingerprintAttendanceViewSet, basename='attendance')


urlpatterns = [
    path('register/', StudentRegisterView.as_view(), name='student-register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('fingerprint/upload/', FingerprintUploadView.as_view(), name='fingerprint-upload'),
    path('attendance/scan/', FingerprintAttendanceView.as_view(), name='attendance-scan'),
    path('admin/attendance-report/', AdminAttendanceReportView.as_view(), name='admin-attendance-report'),
    path('admin/attendance-update/<int:id>/', AdminAttendanceUpdateView.as_view(), name='admin-attendance-update'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('lecturer/dashboard/', LecturerAttendanceDashboard.as_view(), name='lecturer-dashboard'),
    path('admin/dashboard/', AdminAttendanceDashboard.as_view(), name='admin-dashboard'),
    path('', include(router.urls)),
    path('lecturer/login/', LecturerLoginView.as_view(), name='lecturer-login'),
]
