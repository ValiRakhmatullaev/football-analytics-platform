"""Video match creation API."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class VideoCreateMatchAPIView(APIView):
    """Create a match from video."""
    
    def post(self, request, video_id):
        return Response({'match_id': None}, status=status.HTTP_201_CREATED)
