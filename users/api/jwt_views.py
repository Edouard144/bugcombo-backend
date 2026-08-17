from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.api.serializers import UserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            access = response.data['access']
            refresh = response.data['refresh']
            user = self.user
            return Response({
                'user': UserSerializer(user).data,
                'access': access,
                'refresh': refresh,
            }, status=status.HTTP_200_OK)
        return response


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            access = response.data['access']
            return Response({
                'access': access,
            }, status=status.HTTP_200_OK)
        return response
