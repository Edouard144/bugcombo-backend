from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import Snippet, SnippetLike
from .serializers import SnippetSerializer, SnippetCreateSerializer, SnippetLikeSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse

class SnippetListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Snippets'],
        summary='List snippets',
        description='Get all public snippets, or user snippets if authenticated.',
        parameters=[
            OpenApiParameter(name='language', description='Filter by language', required=False, type=str),
            OpenApiParameter(name='search', description='Search in title', required=False, type=str),
            OpenApiParameter(name='user_id', description='Filter by creator user ID', required=False, type=int),
        ],
        responses={200: OpenApiResponse(response=SnippetSerializer(many=True))}
    )
    def get(self, request):
        snippets = Snippet.objects.filter(is_public=True)
        language = request.query_params.get('language')
        search = request.query_params.get('search')
        user_id = request.query_params.get('user_id')
        if language:
            snippets = snippets.filter(language=language)
        if search:
            snippets = snippets.filter(title__icontains=search)
        if user_id:
            snippets = snippets.filter(created_by_id=user_id)
        serializer = SnippetSerializer(snippets, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        tags=['Snippets'],
        summary='Create snippet',
        description='Create a new code snippet.',
        request=SnippetCreateSerializer,
        responses={
            201: OpenApiResponse(response=SnippetSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Validation error'),
        }
    )
    def post(self, request):
        serializer = SnippetCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            snippet = serializer.save()
            return Response(SnippetSerializer(snippet, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SnippetDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Snippets'],
        summary='Snippet detail',
        description='Get a specific snippet.',
        parameters=[
            OpenApiParameter(name='snippet_id', description='Snippet ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=SnippetSerializer),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Snippet not found or private'),
        }
    )
    def get(self, request, snippet_id):
        snippet = get_object_or_404(Snippet, id=snippet_id)
        if not snippet.is_public and snippet.created_by != request.user:
            return Response({'error': 'Private snippet'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SnippetSerializer(snippet, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        tags=['Snippets'],
        summary='Update snippet',
        description='Update a snippet. Only the creator can update.',
        parameters=[
            OpenApiParameter(name='snippet_id', description='Snippet ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        request=SnippetCreateSerializer,
        responses={
            200: OpenApiResponse(response=SnippetSerializer),
            403: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Not the creator'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Snippet not found'),
        }
    )
    def put(self, request, snippet_id):
        snippet = get_object_or_404(Snippet, id=snippet_id)
        if snippet.created_by != request.user:
            return Response({'error': 'Not the creator'}, status=status.HTTP_403_FORBIDDEN)
        serializer = SnippetCreateSerializer(snippet, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(SnippetSerializer(snippet, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Snippets'],
        summary='Delete snippet',
        description='Delete a snippet. Only the creator can delete.',
        parameters=[
            OpenApiParameter(name='snippet_id', description='Snippet ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            204: None,
            403: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Not the creator'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Snippet not found'),
        }
    )
    def delete(self, request, snippet_id):
        snippet = get_object_or_404(Snippet, id=snippet_id)
        if snippet.created_by != request.user:
            return Response({'error': 'Not the creator'}, status=status.HTTP_403_FORBIDDEN)
        snippet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class LikeSnippetView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Snippets'],
        summary='Like snippet',
        description='Like a snippet.',
        parameters=[
            OpenApiParameter(name='snippet_id', description='Snippet ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            201: OpenApiResponse(response=SnippetLikeSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Already liked'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Snippet not found'),
        }
    )
    def post(self, request, snippet_id):
        snippet = get_object_or_404(Snippet, id=snippet_id)
        existing = SnippetLike.objects.filter(snippet=snippet, user=request.user).first()
        if existing:
            return Response({'error': 'Already liked'}, status=status.HTTP_400_BAD_REQUEST)
        like = SnippetLike.objects.create(snippet=snippet, user=request.user)
        serializer = SnippetLikeSerializer(like)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UnlikeSnippetView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Snippets'],
        summary='Unlike snippet',
        description='Remove like from a snippet.',
        parameters=[
            OpenApiParameter(name='snippet_id', description='Snippet ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Unliked'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Snippet not found or not liked'),
        }
    )
    def post(self, request, snippet_id):
        snippet = get_object_or_404(Snippet, id=snippet_id)
        try:
            like = SnippetLike.objects.get(snippet=snippet, user=request.user)
            like.delete()
            return Response({'ok': True})
        except SnippetLike.DoesNotExist:
            return Response({'error': 'Not liked'}, status=status.HTTP_404_NOT_FOUND)

class MySnippetsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Snippets'],
        summary='My snippets',
        description='Get all snippets created by the authenticated user.',
        responses={200: OpenApiResponse(response=SnippetSerializer(many=True))}
    )
    def get(self, request):
        snippets = Snippet.objects.filter(created_by=request.user)
        serializer = SnippetSerializer(snippets, many=True, context={'request': request})
        return Response(serializer.data)
