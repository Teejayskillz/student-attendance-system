from django.shortcuts import render
from rest_framework import generics, permissions
from .models import User
from .serializers import UserSerializer
from rest_framework.response import Response

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import CourseSerializer, ClassSessionSerializer
from .permissions import IsLecturer, IsStudent
from rest_framework.permissions import IsAuthenticated



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



