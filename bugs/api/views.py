from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from ..models import Bug
from .serializers import BugSerializer, BugListSerializer

class BugListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bugs = Bug.objects.all()

        language = request.query_params.get('language')
        if language:
            bugs = bugs.filter(language=language)

        difficulty = request.query_params.get('difficulty')
        if difficulty:
            bugs = bugs.filter(difficulty=difficulty)

        search = request.query_params.get('search')
        if search:
            bugs = bugs.filter(title__icontains=search)

        ordering = request.query_params.get('ordering', '-created_at')
        if ordering in ['created_at', '-created_at', 'avg_score', '-avg_score', 'times_used', '-times_used']:
            bugs = bugs.order_by(ordering)

        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        start = (page - 1) * limit
        end = start + limit
        total = bugs.count()
        page_bugs = bugs[start:end]

        serializer = BugListSerializer(page_bugs, many=True)
        return Response({
            'count': total,
            'page': page,
            'limit': limit,
            'results': serializer.data
        })

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

class FeaturedBugsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        bugs = Bug.objects.order_by('-avg_score', '-times_used')[:10]
        serializer = BugListSerializer(bugs, many=True)
        return Response(serializer.data)

class RandomBugView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        language = request.query_params.get('language')
        difficulty = request.query_params.get('difficulty')
        bugs = Bug.objects.all()
        if language:
            bugs = bugs.filter(language=language)
        if difficulty:
            bugs = bugs.filter(difficulty=difficulty)
        bug = bugs.order_by('?').first()
        if not bug:
            return Response({'error': 'No bugs found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BugListSerializer(bug)
        return Response(serializer.data)
