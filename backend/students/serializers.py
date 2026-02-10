from rest_framework import serializers
from .models import User, Course, ClassSession, Attendance
from django.contrib.auth import authenticate


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

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'lecturer', 'students']

class ClassSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSession
        fields = ['id', 'course', 'start_time', 'end_time', 'is_active']


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

class ClassSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSession
        fields = ['id', 'course', 'start_time', 'end_time', 'is_active']
        read_only_fields = ['start_time', 'end_time', 'is_active']

class FingerprintUploadSerializer(serializers.Serializer):
    fingerprint_template = serializers.CharField(write_only=True)

class FingerprintAttendanceSerializer(serializers.Serializer):
    fingerprint_template = serializers.CharField()
    session_id = serializers.IntegerField()

class AttendanceReportSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.username', read_only=True)
    course_name = serializers.CharField(source='class_session.course.name', read_only=True)
    session_start = serializers.DateTimeField(source='class_session.start_time', read_only=True)
    session_end = serializers.DateTimeField(source='class_session.end_time', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'student_name', 'course_name', 'session_start', 'session_end', 'status', 'timestamp']

class AttendanceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['status']  # allow changing 'present' or 'absent'

class LecturerLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        email = attrs.get("email")
        password = attrs.get("password")

        if not password:
            raise serializers.ValidationError("Password is required.")
        if not username and not email:
            raise serializers.ValidationError("Provide username or email.")

        # Default Django auth uses username, so:
        user = None
        if username:
            user = authenticate(username=username, password=password)
        else:
            # email -> get username -> authenticate
            try:
                u = User.objects.get(email=email)
                user = authenticate(username=u.username, password=password)
            except User.DoesNotExist:
                user = None

        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("Account disabled.")
        if user.role != "lecturer":
            raise serializers.ValidationError("Lecturers only.")

        attrs["user"] = user
        return attrs


class LecturerMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role"]
