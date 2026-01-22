from django.contrib import admin
from .models import User, Course, ClassSession, Attendance, ScannerDevice, AttendanceLog

# Customizing User admin
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email')

# Course admin
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'lecturer')
    list_filter = ('lecturer',)
    search_fields = ('name', 'lecturer__username')

# ClassSession admin
@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ('course', 'start_time', 'end_time', 'is_active')
    list_filter = ('course', 'is_active')
    search_fields = ('course__name',)

# Attendance admin
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_session', 'status', 'timestamp')
    list_filter = ('status', 'class_session__course')
    search_fields = ('student__username', 'class_session__course__name')

# ScannerDevice admin
@admin.register(ScannerDevice)
class ScannerDeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_key', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'api_key')

# AttendanceLog admin
@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'scanner', 'timestamp')
    list_filter = ('scanner', 'timestamp')
    search_fields = ('student__username', 'scanner__name')
