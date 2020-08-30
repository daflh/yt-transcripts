from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qsl
from youtube_transcript_api import YouTubeTranscriptApi
import json

# don't know how to dynamically get scheme & netloc
host = "https://yt-transcripts.vercel.app"

def fetch(video_id, lang_code = [], translate_to = None, transcript_type = ""):
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    if transcript_type == "manual":
        methodToFind = "find_manually_created_transcript"
    elif transcript_type == "generated":
        methodToFind = "find_generated_transcript"
    else:
        # this method will find regardless of the type
        # but manually created takes precedence
        methodToFind = "find_transcript"
    
    # if "lang_code" list is empty, search for english transcript, then search
    # from the list of available languages of the video
    if len(lang_code) == 0:
        available_lang = list(map(
            lambda n: n.language_code,
            list(transcript_list)
        ))
        lang_code = ["en", *available_lang]

    transcript = getattr(transcript_list, methodToFind)(lang_code)
    # it will contains original language of the translation
    original_lang = None

    if translate_to != None:
        original_lang = transcript.language_code
        transcript = transcript.translate(translate_to)
        
    return {
        "lang_code": transcript.language_code,
        "translated_from": original_lang,
        "transcript_type": "generated" if transcript.is_generated else "manual",
        "data": transcript.fetch()
    }

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # this will take the last parameter if it's more than 1
        q = dict(parse_qsl(urlparse(self.path).query))

        message = ""
        responses = {}
        
        try:
            assert "v" in q, "Missing required parameter 'v'"

            # arguments to pass to "fetch" func
            args = {}
            args["video_id"] = q["v"]

            assert len(q["v"]) == 11, "Invalid video ID"

            responses["transcript_list_url"] = host + "/list?v=" + q["v"]

            if "lang" in q:
                args["lang_code"] = q["lang"].split(",")
            if "tl" in q:
                args["translate_to"] = q["tl"]
            if "type" in q and q["type"] in ["generated", "manual"]:
                args["transcript_type"] = q["type"]

            responses.update({
                "request_params": args
            })
            transcript = fetch(**args)
            responses.update(transcript)
            
        except Exception as e:
            _msg = str(e)
            # get CAUSE_MESSAGE of YouTubeTranscriptApi errors
            if "CAUSE_MESSAGE" in dir(e):
                cause = str(getattr(e, "CAUSE_MESSAGE"))
                # only for NoTranscriptFound error
                _msg = cause.split(":")[0] if ":" in cause else cause

            message = _msg
            responses["data"] = []

        status_code = 200 if message == "" else 400
        responses = json.dumps({
            "is_error": False if message == "" else True,
            "message": message,
            **responses
        }).encode()

        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(responses)
        return