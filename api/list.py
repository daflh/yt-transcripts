from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
import json

host = "https://yt-transcripts.vercel.app"

def transcript_list(video_id):
    neat_transcript_list = []
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    for transcript in transcript_list:
        neat_transcript_list.append({
            "lang": transcript.language,
            "lang_code": transcript.language_code,
            "transcript_type": "generated" if transcript.is_generated else "manual",
            "translatable": transcript.is_translatable
        })

    return neat_transcript_list

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        message = ""
        info = {}
        data = []
        query = parse_qs(urlparse(self.path).query)
        
        try:
            assert "v" in query, "Missing required parameter 'v'"

            video_id = query["v"][0]
            assert len(video_id) == 11, "Invalid video ID"
            info["video_id"] = video_id
            info["video_url"] = f"https://www.youtube.com/watch?v={video_id}"

            def dictAddUrl(n):
                n["url"] = f"{host}/get?v={video_id}&lang={n['lang_code']}&type={n['transcript_type']}"
                return n
            data = list(map(dictAddUrl, transcript_list(video_id)))
            
        except Exception as err:
            if "CAUSE_MESSAGE" in dir(err):
                _msg = str(getattr(err, "CAUSE_MESSAGE"))
                message = _msg if ":" not in _msg else _msg.split(":")[0]
            else:
                message = str(err)

        is_error = False if message == "" else True
        if is_error:
            info["message"] = message

        response = json.dumps({
            "is_error": is_error,
            **info,
            "data": data
        }).encode()

        self.send_response(400 if is_error else 200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(response)
        return