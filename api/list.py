from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
import json

def transcript_list(video_id):
    neat_transcript_list = []
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    for transcript in transcript_list:
        neat_transcript_list.append({
            "lang": transcript.language,
            "lang_code": transcript.language_code,
            "type": 2 if transcript.is_generated else 1,
            "translatable": transcript.is_translatable
        })

    return neat_transcript_list

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        message = ""
        data = []
        query = parse_qs(urlparse(self.path).query)
        
        if "v" not in query:
            message = "'v' parameter is required"
        else:
            video_id = query["v"][0]
            if len(video_id) != 11:
                message = "Invalid video ID"
            else:
                try:
                    data = transcript_list(video_id)
                except:
                    message = "No subtitle found in this video"

        res = json.dumps({
            "isError": True if message != "" else False,
            "message": message,
            "data": data
        }).encode()

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(res)
        return