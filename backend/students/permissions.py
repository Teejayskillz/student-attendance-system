from rest_framework.permissions import BasePermission

class IsLecturer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'lecturer'


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'

class IsValidScanner(BasePermission):
    def has_permission(self, request, view):
        api_key = request.headers.get("X-SCANNER-KEY")
        return ScannerDevice.objects.filter(
            api_key=api_key,
            is_active=True
        ).exists()
