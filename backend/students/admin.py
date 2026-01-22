from django.contrib import admin
from .models import User, Course, ClassSession, Attendance

admin.site.register(User)
admin.site.register(Course)
admin.site.register(ClassSession)
admin.site.register(Attendance)