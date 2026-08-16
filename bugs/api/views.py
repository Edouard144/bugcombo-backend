from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.http import FileResponse
from io import StringIO
import json
import csv
from ..models import Bug
from .serializers import BugSerializer, BugListSerializer
from core.permissions import IsBugCreator, IsAdminOrReadOnly
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse

class BugListCreateView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    @extend_schema(
        tags=['Bugs'],
        summary='List and create bugs',
        description='List bugs with optional filtering by language, difficulty, and search. Admin users can create new bugs. Supports pagination and ordering.',
        parameters=[
            OpenApiParameter(name='language', description='Filter by programming language', required=False, type=str),
            OpenApiParameter(name='difficulty', description='Filter by difficulty', required=False, type=str),
            OpenApiParameter(name='search', description='Search in title', required=False, type=str),
            OpenApiParameter(name='ordering', description='Order by field', required=False, type=str),
            OpenApiParameter(name='page', description='Page number', required=False, type=int),
            OpenApiParameter(name='limit', description='Items per page', required=False, type=int),
        ],
        responses={
            200: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Paginated bug list'),
            201: OpenApiResponse(response=BugSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Validation error'),
        }
    )
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

    @extend_schema(
        tags=['Bugs'],
        summary='Create bug',
        description='Create a new bug. Admin only.',
        request=BugSerializer,
        responses={
            201: OpenApiResponse(response=BugSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Validation error'),
        }
    )
    def post(self, request):
        serializer = BugSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BugDetailView(APIView):
    permission_classes = [IsAuthenticated, IsBugCreator]

    @extend_schema(
        tags=['Bugs'],
        summary='Bug detail',
        description='Retrieve, update, or delete a specific bug. Only the bug creator or admin can modify or delete.',
        parameters=[
            OpenApiParameter(name='pk', description='Bug UUID', required=True, type=str, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=BugSerializer),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Bug not found'),
        }
    )
    def get(self, request, pk):
        try:
            bug = Bug.objects.get(pk=pk)
            serializer = BugSerializer(bug)
            return Response(serializer.data)
        except Bug.DoesNotExist:
            return Response({'error': 'Bug not found'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=['Bugs'],
        summary='Update bug',
        description='Partially update a bug. Only the bug creator or admin can update.',
        parameters=[
            OpenApiParameter(name='pk', description='Bug UUID', required=True, type=str, location=OpenApiParameter.PATH)
        ],
        request=BugSerializer,
        responses={
            200: OpenApiResponse(response=BugSerializer),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Bug not found'),
        }
    )
    def put(self, request, pk):
        try:
            bug = Bug.objects.get(pk=pk)
            self.check_object_permissions(request, bug)
            serializer = BugSerializer(bug, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Bug.DoesNotExist:
            return Response({'error': 'Bug not found'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=['Bugs'],
        summary='Delete bug',
        description='Delete a bug permanently. Only the bug creator or admin can delete.',
        parameters=[
            OpenApiParameter(name='pk', description='Bug UUID', required=True, type=str, location=OpenApiParameter.PATH)
        ],
        responses={
            204: None,
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Bug not found'),
        }
    )
    def delete(self, request, pk):
        try:
            bug = Bug.objects.get(pk=pk)
            self.check_object_permissions(request, bug)
            bug.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Bug.DoesNotExist:
            return Response({'error': 'Bug not found'}, status=status.HTTP_404_NOT_FOUND)

class FeaturedBugsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Bugs'],
        summary='Featured bugs',
        description='Get the top 10 bugs ranked by average score and usage count.',
        responses={200: OpenApiResponse(response=BugListSerializer(many=True))}
    )
    def get(self, request):
        bugs = Bug.objects.order_by('-avg_score', '-times_used')[:10]
        serializer = BugListSerializer(bugs, many=True)
        return Response(serializer.data)

class RandomBugView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Bugs'],
        summary='Random bug',
        description='Get a random bug, optionally filtered by language and difficulty.',
        parameters=[
            OpenApiParameter(name='language', description='Filter by programming language', required=False, type=str),
            OpenApiParameter(name='difficulty', description='Filter by difficulty', required=False, type=str),
        ],
        responses={
            200: OpenApiResponse(response=BugListSerializer),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='No bugs found'),
        }
    )
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


class BugExportView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=['Bugs'],
        summary='Export bugs',
        description='Export all bugs as JSON or CSV file. Admin only.',
        parameters=[
            OpenApiParameter(name='format', description='Export format', required=False, type=str, enum=['json', 'csv'])
        ],
        responses={
            200: OpenApiResponse(response=OpenApiTypes.OBJECT, description='File download'),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Invalid format'),
        }
    )
    def get(self, request):
        fmt = request.query_params.get('format', 'json')
        bugs = Bug.objects.all()

        if fmt == 'csv':
            buffer = StringIO()
            writer = csv.writer(buffer)
            writer.writerow(['id', 'title', 'description', 'language', 'difficulty', 'starter_code', 'test_cases', 'created_by', 'times_used', 'avg_score', 'created_at'])
            for bug in bugs:
                writer.writerow([
                    str(bug.id), bug.title, bug.description, bug.language, bug.difficulty,
                    bug.starter_code, json.dumps(bug.test_cases), str(bug.created_by_id),
                    bug.times_used, bug.avg_score, bug.created_at.isoformat()
                ])
            buffer.seek(0)
            response = FileResponse(buffer, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="bugs.csv"'
            return response

        data = []
        for bug in bugs:
            data.append({
                'id': str(bug.id),
                'title': bug.title,
                'description': bug.description,
                'language': bug.language,
                'difficulty': bug.difficulty,
                'starter_code': bug.starter_code,
                'test_cases': bug.test_cases,
                'created_by': str(bug.created_by_id),
                'times_used': bug.times_used,
                'avg_score': bug.avg_score,
                'created_at': bug.created_at.isoformat(),
                'updated_at': bug.updated_at.isoformat(),
            })
        response = FileResponse(
            StringIO(json.dumps(data, indent=2)),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="bugs.json"'
        return response


class BugImportView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=['Bugs'],
        summary='Import bugs',
        description='Import bugs from a JSON file. Creates new bugs or updates existing ones by ID. Admin only.',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'JSON file containing bug data'
                    }
                }
            }
        },
        responses={
            201: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Import result with created/updated/skipped counts'),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Invalid file or JSON'),
        }
    )
    def post(self, request):
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'error': 'File is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            content = uploaded.read().decode('utf-8')
            data = json.loads(content)
        except Exception as e:
            return Response({'error': f'Invalid JSON: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(data, list):
            data = [data]

        created = 0
        updated = 0
        skipped = 0

        for item in data:
            try:
                bug_id = item.get('id')
                if bug_id:
                    bug, was_created = Bug.objects.update_or_create(
                        id=bug_id,
                        defaults={
                            'title': item.get('title', ''),
                            'description': item.get('description', ''),
                            'language': item.get('language', 'python'),
                            'difficulty': item.get('difficulty', 'easy'),
                            'starter_code': item.get('starter_code', ''),
                            'test_cases': item.get('test_cases', []),
                            'times_used': item.get('times_used', 0),
                            'avg_score': item.get('avg_score', 0.0),
                        }
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1
                else:
                    Bug.objects.create(
                        title=item.get('title', ''),
                        description=item.get('description', ''),
                        language=item.get('language', 'python'),
                        difficulty=item.get('difficulty', 'easy'),
                        starter_code=item.get('starter_code', ''),
                        test_cases=item.get('test_cases', []),
                        times_used=item.get('times_used', 0),
                        avg_score=item.get('avg_score', 0.0),
                    )
                    created += 1
            except Exception as e:
                skipped += 1

        return Response({
            'created': created,
            'updated': updated,
            'skipped': skipped,
        }, status=status.HTTP_201_CREATED)
