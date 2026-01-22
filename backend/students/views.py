from django.shortcuts import render
from rest_framework import generics, permissions
from .models import User, Attendance, ClassSession
from rest_framework import viewsets, status
from rest_framework.decorators import action
from .serializers import UserSerializer, CourseSerializer, ClassSessionSerializer, FingerprintUploadSerializer, FingerprintAttendanceSerializer, AttendanceReportSerializer, AttendanceUpdateSerializer
from .permissions import IsLecturer, IsStudent , IsValidScanner 
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.response import Response


# Register a student
class StudentRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]  # public endpoint


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Admin can see all courses
        if user.role == 'admin':
            return Course.objects.all()

        # Lecturer sees only courses they teach
        if user.role == 'lecturer':
            return Course.objects.filter(lecturer=user)

        # Student sees courses they enrolled in
        if user.role == 'student':
            return Course.objects.filter(students=user)

        return Course.objects.none()

    def perform_create(self, serializer):
        # Only lecturers can create courses
        if self.request.user.role != 'lecturer':
            raise PermissionError("Only lecturers can create courses")

        serializer.save(lecturer=self.request.user)
    
    #students enroll in a course
    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def enroll(self, request, pk=None):
        course = self.get_object()
        student = request.user

        if student in course.students.all():
            return Response(
                {"message": "Already enrolled"},
                status=status.HTTP_400_BAD_REQUEST
            )

        course.students.add(student)
        return Response(
            {"message": "Successfully enrolled in course"},
            status=status.HTTP_200_OK
        )

        #lecturer view enrolled students
    @action(detail=True, methods=['get'], permission_classes=[IsLecturer])
    def students(self, request, pk=None):
        course = self.get_object()

        students = course.students.all().values(
            'id', 'username', 'email'
        )

        return Response(students)


class ClassSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSessionSerializer
    permission_classes = [IsLecturer]

    def get_queryset(self):
        # Lecturer sees only sessions for their courses
        return ClassSession.objects.filter(
            course__lecturer=self.request.user
        )

    #started class session
    @action(detail=False, methods=['post'])
    def start(self, request):
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {"error": "course_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            course = Course.objects.get(
                id=course_id,
                lecturer=request.user
            )
        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found or not yours"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if session already active
        if ClassSession.objects.filter(course=course, is_active=True).exists():
            return Response(
                {"error": "An active session already exists for this course"},
                status=status.HTTP_400_BAD_REQUEST
            )

        session = ClassSession.objects.create(
            course=course,
            start_time=timezone.now(),
            is_active=True
        )

        return Response(
            {
                "message": "Class session started",
                "session_id": session.id
            },
            status=status.HTTP_201_CREATED
        )
    
    #ended class session
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        try:
            session = self.get_object()
        except ClassSession.DoesNotExist:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if not session.is_active:
            return Response(
                {"error": "Session already ended"},
                status=status.HTTP_400_BAD_REQUEST
            )

        session.is_active = False
        session.end_time = timezone.now()
        session.save()

        return Response(
            {"message": "Class session ended"},
            status=status.HTTP_200_OK
        )

#views to upload fingerprint
class FingerprintUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'student':
            return Response(
                {"error": "Only students can upload fingerprints"},
                status=403
            )

        serializer = FingerprintUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.user.fingerprint_hash:
            return Response(
                {"error": "Fingerprint already registered"},
                status=409
            )

        request.user.set_fingerprint(
            serializer.validated_data['fingerprint_template']
        )
        request.user.save()

        return Response({"message": "Fingerprint registered successfully"})


class FingerprintAttendanceView(APIView):
    authentication_classes = []   # scanner doesn’t login like users
    permission_classes = [IsValidScanner]

    def post(self, request):
        serializer = FingerprintAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fingerprint = serializer.validated_data['fingerprint_template']
        # 1️⃣ Find student (secure fingerprint matching)
        student = None

        for s in User.objects.filter(role='student', fingerprint_hash__isnull=False):
            if s.check_fingerprint(fingerprint):
                student = s
                break


        if not student:
            return Response(
                {"error": "Fingerprint not recognized"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2️⃣ Find active session
        session = ClassSession.objects.filter(is_active=True).select_related('course').first()

        if not session:
            return Response(
                {"error": "No active class session"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3️⃣ Check enrollment
        if not session.course.students.filter(id=student.id).exists():
            return Response(
                {"error": "Student not enrolled for this course"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 4️⃣ Prevent duplicate attendance
        if Attendance.objects.filter(student=student, class_session=session).exists():
            return Response(
                {"error": "Attendance already marked"},
                status=status.HTTP_409_CONFLICT
            )

        # 5️⃣ Mark attendance
        Attendance.objects.create(
            student=student,
            class_session=session,
            status='present',
            timestamp=timezone.now()
        )

        return Response(
            {
                "message": "Attendance marked successfully",
                "student": student.username,
                "course": session.course.name
            },
            status=status.HTTP_201_CREATED
        )
#only registered scanners can mark attendance 
class FingerprintAttendanceView(APIView):
    permission_classes = [IsValidScanner]


class AdminAttendanceReportView(generics.ListAPIView):
    serializer_class = AttendanceReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != 'admin':
            return Attendance.objects.none()  # only admins can access
        course_id = self.request.query_params.get('course_id')
        student_id = self.request.query_params.get('student_id')
        queryset = Attendance.objects.all()
        if course_id:
            queryset = queryset.filter(class_session__course__id=course_id)
        if student_id:
            queryset = queryset.filter(student__id=student_id)
        return queryset.order_by('-timestamp')


class AdminAttendanceUpdateView(generics.UpdateAPIView):
    serializer_class = AttendanceUpdateSerializer
    permission_classes = [IsAuthenticated]
    queryset = Attendance.objects.all()
    lookup_field = 'id'

    def get_queryset(self):
        if self.request.user.role != 'admin':
            return Attendance.objects.none()
        return super().get_queryset()



class AdminUserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != 'admin':
            return User.objects.none()
        role = self.request.query_params.get('role')  # optional: filter by student/lecturer
        qs = User.objects.all()
        if role in ['student', 'lecturer']:
            qs = qs.filter(role=role)
        return qs


class LecturerAttendanceDashboard(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'lecturer':
            return Response({"error": "Only lecturers allowed"}, status=403)

        dashboard = []

        for course in request.user.courses_taught.all():
            sessions_data = []
            for session in course.classsession_set.all().order_by('-start_time'):
                attendances = session.attendance_set.all()
                sessions_data.append({
                    "session_id": session.id,
                    "start_time": session.start_time,
                    "end_time": session.end_time,
                    "is_active": session.is_active,
                    "total_students": course.students.count(),
                    "present_students": attendances.filter(status='present').count(),
                    "absent_students": attendances.filter(status='absent').count()
                })
            dashboard.append({
                "course_id": course.id,
                "course_name": course.name,
                "sessions": sessions_data
            })

        return Response(dashboard)

class AdminAttendanceDashboard(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'admin':
            return Response({"error": "Only admins allowed"}, status=403)

        data = []
        courses = Course.objects.all()
        for course in courses:
            sessions = []
            for session in course.classsession_set.all().order_by('-start_time'):
                attendances = session.attendance_set.all()
                sessions.append({
                    "session_id": session.id,
                    "course_name": course.name,
                    "start_time": session.start_time,
                    "end_time": session.end_time,
                    "is_active": session.is_active,
                    "present": attendances.filter(status='present').count(),
                    "absent": attendances.filter(status='absent').count()
                })
            data.append({
                "course_id": course.id,
                "course_name": course.name,
                "sessions": sessions
            })
        return Response(data)
