from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, _errors as TranscriptError
import json

host = "https://yt-transcript.vercel.app"

def get_transcript(video_id, lang_code, transcript_type, translate_to = None):
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    if transcript_type == "manual":
        methodToFind = "find_manually_created_transcript"
    elif transcript_type == "generated":
        methodToFind = "find_generated_transcript"
    elif transcript_type == "both":
        methodToFind = "find_transcript"
    transcript = getattr(transcript_list, methodToFind)(lang_code)

    if translate_to != None:
        transcript = transcript.translate(translate_to)
        
    return transcript.fetch()

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        message = ""
        info = {}
        data = []
        query = parse_qs(urlparse(self.path).query)
        
        try:
            if "v" not in query:
                raise Exception("'v' parameter is required")

            video_id = query["v"][0]
            if len(video_id) != 11:
                raise Exception("Invalid video ID")
            info["video_id"] = video_id
            info["transcript_list_url"] = f"{host}/list?v={video_id}"

            args = {}

            if "lang" in query:
                args["lang_code"] = query["lang"][0].split(",")
            else:
                args["lang_code"] = ["en"]

            if "type" in query:
                if query["type"][0] not in ("manual", "generated", "both"):
                    raise Exception("Invalid transcript type, use manual, generated, or both")
                args["transcript_type"] = query["type"][0]
            else:
                args["transcript_type"] = "both"

            if "translate" in query:
                translate_to = query["translate"][0]
                args["translate_to"] = translate_to

            info.update(args)
            data = get_transcript(video_id, **args)

        except (TranscriptError.NoTranscriptFound, TranscriptError.TranscriptsDisabled):
            message = f"No transcript found"

        except TranscriptError.TranslationLanguageNotAvailable:
            message = f"Translation to language '{translate_to}' is not available"
            
        except Exception as err:
            message = str(err)

        is_error = False if message == "" else True
        if is_error:
            info["message"] = message

        if "lang_code" in info and len(info["lang_code"]) == 1:
            info["lang_code"] = info["lang_code"][0]

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