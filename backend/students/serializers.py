from rest_framework import serializers
from .models import User, Course, ClassSession, Attendance

# User Serializer
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'fingerprint_template']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

# Course Serializer
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'lecturer', 'students']

# Class Session Serializer
class ClassSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSession
        fields = ['id', 'course', 'start_time', 'end_time', 'is_active']

# Attendance Serializer
class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['id', 'student', 'class_session', 'status', 'timestamp']

class CourseSerializer(serializers.ModelSerializer):
    lecturer = serializers.ReadOnlyField(source='lecturer.id')

    class Meta:
        model = Course
        fields = ['id', 'name', 'lecturer', 'students']
        read_only_fields = ['students']
