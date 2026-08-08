from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from ..models import Bug
from .serializers import BugSerializer

class BugListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bugs = Bug.objects.all()
        serializer = BugSerializer(bugs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BugSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BugDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            bug = Bug.objects.get(pk=pk)
            serializer = BugSerializer(bug)
            return Response(serializer.data)
        except Bug.DoesNotExist:
            return Response({'error': 'Bug not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            bug = Bug.objects.get(pk=pk)
            if bug.created_by != request.user:
                return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
            serializer = BugSerializer(bug, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Bug.DoesNotExist:
            return Response({'error': 'Bug not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            bug = Bug.objects.get(pk=pk)
            if bug.created_by != request.user:
                return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
            bug.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Bug.DoesNotExist:
            return Response({'error': 'Bug not found'}, status=status.HTTP_404_NOT_FOUND)
