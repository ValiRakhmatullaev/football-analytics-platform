"""Video JSON download API."""
from rest_framework.views import APIView
from rest_framework.response import Response


class VideoJSONDownloadAPIView(APIView):
    """Download video events as JSON."""
    
    def get(self, request, video_id):
        return Response({'events': []})
