from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope, TokenHasScope
import requests

class ComplexOp(APIView):
    def post(self, request):
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
