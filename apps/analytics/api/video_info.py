"""Video info API."""
from rest_framework.views import APIView
from rest_framework.response import Response


class VideoInfoAPIView(APIView):
    """Get video info."""
    
    def get(self, request, video_id):
        return Response({'id': video_id, 'status': 'completed'})


class VideoListAPIView(APIView):
    """List all videos."""
    
    def get(self, request):
        return Response([])
