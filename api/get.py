from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, _errors as TranscriptError
import json

def get_transcript(video_id, lang = ["en"], tlType = 0, translate = None):
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    if tlType == 1:
        methodToFind = "find_manually_created_transcript"
    elif tlType == 2:
        methodToFind = "find_generated_transcript"
    else:
        methodToFind = "find_transcript"
    transcript = getattr(transcript_list, methodToFind)(lang)
    if translate != None:
        transcript = transcript.translate(translate)
    return transcript.fetch()

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        message = ""
        data = []
        query = parse_qs(urlparse(self.path).query)
        
        try:
            if "v" not in query:
                raise Exception("'v' parameter is required")
            video_id = query["v"][0]
            if len(video_id) != 11:
                raise Exception("Invalid video ID")
            optArgs = {}
            if "lang" in query:
                optArgs["lang"] = query["lang"][0].split(",")
            if "type" in query:
                optArgs["tlType"] = int(query["type"][0])
            if "translate" in query:
                translateTo = query["translate"][0]
                optArgs["translate"] = translateTo
            data = get_transcript(video_id, **optArgs)

        except TranscriptError.NoTranscriptFound:
            message = "No transcript(s) were found"

        except TranscriptError.TranslationLanguageNotAvailable:
            message = f"Translation to language '{translateTo}' is not available"
            
        except Exception as err:
            message = str(err)

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