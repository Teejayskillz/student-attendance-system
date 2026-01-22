from django.contrib.auth.models import AbstractUser
from django.db import models
import hashlib

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('lecturer', 'Lecturer'),
        ('student', 'Student'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    fingerprint_template = models.CharField(max_length=256, blank=True, null=True)

    def set_fingerprint(self, raw_fingerprint):
        self.fingerprint_template = hashlib.sha256(
            raw_fingerprint.encode()
        ).hexdigest()

    def check_fingerprint(self, raw_fingerprint):
        return self.fingerprint_template == hashlib.sha256(
            raw_fingerprint.encode()
        ).hexdigest()

class Course(models.Model):
    name = models.CharField(max_length=100)
    lecturer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'lecturer'},
        related_name="courses_taught"   # unique reverse accessor
    )
    students = models.ManyToManyField(
        User,
        limit_choices_to={'role': 'student'},
        blank=True,
        related_name="courses_enrolled"  # unique reverse accessor
    )

    def __str__(self):
        return self.name


class ClassSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.course.name} - {self.start_time}"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role':'student'})
    class_session = models.ForeignKey(ClassSession, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.class_session} - {self.status}"


class ScannerDevice(models.Model):
    name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
# Generates a unique API key automatically
#Admin can deactivate a scanner if needed
    def __str__(self):
        return f"{self.name} - {'Active' if self.is_active else 'Inactive'}"

class AttendanceLog(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    scanner = models.ForeignKey(ScannerDevice, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
