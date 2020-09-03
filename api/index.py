from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qsl
from youtube_transcript_api import YouTubeTranscriptApi
import json, re, math

# don't know how to get scheme & netloc dynamically
host = "https://yt-transcripts.vercel.app"

def _list(video_id):
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    neat_transcript_list = []

    # loop through list of available languages in this videos
    # then return the "neat" list, basically same but more readable
    for transcript in transcript_list:
        lang_code = transcript.language_code
        transcript_type = "generated" if transcript.is_generated else "manual"
        neat_transcript_list.append({
            "lang": transcript.language,
            "lang_code": lang_code,
            "transcript_type": transcript_type,
            "url": f"{host}/api?v={video_id}&lang={lang_code}&type={transcript_type}"
        })

    return neat_transcript_list

def _find(video_id, lang_code = [], translate_to = None, transcript_type = ""):
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
        # translate to requested language
        transcript = transcript.translate(translate_to)
        
    return [transcript.fetch(), {
        "lang_code": transcript.language_code,
        "translated_from": original_lang,
        "transcript_type": "generated" if transcript.is_generated else "manual"
    }]

def search(data, key, cs = False, marker = ""):
    if "_$_" in marker:
        marker_s, marker_e = marker.split("_$_")[0:2]
    else:
        marker_s = marker_e = marker

    filtered_data = []

    for item in data:
        text = item["text"]
        # this contains an iterator of all "key" substring that appear in "text"
        occurrences = re.finditer(key, text, flags = re.IGNORECASE if not cs else 0)
        # get all start position, then reverse, so that marking starts from behind,
        # and do not mess up the position of "key"(s) in "text"
        starts = list(reversed([m.start() for m in occurrences]))
        if len(starts) > 0:
            for s in starts:
                # "s" stand for start position and "e" stand for end position
                e = s + len(key)
                text = text[:s] + marker_s + text[s:e] + marker_e + text[e:]
            item["text"] = text
            filtered_data.append(item)

    return [filtered_data, {
        "keyword": key,
        "case_sensitive": cs,
        "marker_start": marker_s,
        "marker_end": marker_e,
        "found": len(filtered_data)
    }]

def get(qs):
    message = ""
    responses = {}
    
    try:
        assert "v" in qs, "Missing required parameter 'v'"
        # youtube video ID is always 11 characters in length
        assert len(qs["v"]) == 11, "Invalid video ID, try 'jNQXAC9IVRw' as an example"

        video_id = qs["v"]

        if qs.get("list") == "true":
            responses["video_id"] = video_id
            responses["video_url"] = "https://www.youtube.com/watch?v=" + video_id

            responses["data"] = _list(video_id)

        else:
            # arguments to pass to "fetch" func
            args = {}
            args["video_id"] = video_id

            responses["transcript_list_url"] = f"{host}/api?v={video_id}&list=true"

            if "lang" in qs:
                args["lang_code"] = qs["lang"].split(",")
            if "tl" in qs:
                args["translate_to"] = qs["tl"]
            # ignore if "type" isn't "generated" or "manual"
            if "type" in qs and qs["type"] in ["generated", "manual"]:
                args["transcript_type"] = qs["type"]

            responses["request_params"] = args
            data, attributes = _find(**args)

            responses.update({
                **attributes,
                "found": len(data)
            })

            # if there's "key" in params, return text that contains the value of "key"
            # "cs" and "marker" only used when this param given 
            if "key" in qs:
                case_sens = True if qs.get("cs") == "true" else False
                # use no marker by default
                marker = qs.get("marker", "")
                data, search_attributes = search(data, qs["key"], case_sens, marker)
                # this is just search options (keyword, etc.) and how many text found
                responses["search"] = search_attributes

            # by default, size is 0, which means show all
            size = qs.get("size", "0")
            assert size.isdigit(), "Invalid page number, only positive integers are valid"
            size = int(size)

            if size > 0:
                # these only run when 'size' param is present, showing page 1 by default
                page = qs.get("page", "1")
                # if 'page' param is not digit, return -1, so there will be an assertion error
                page = int(page) if page.isdigit() else -1
                t_pages = math.ceil(len(data) / size)

                assert 1 <= page <= t_pages, f"Invalid page, there are only page 1 until {t_pages}"

                # reduce the value of 'page' by 1 because list index starts with 0
                start = size * (page - 1)
                end = start + size
                data = data[start:end]

                responses.update({
                    "size": size,
                    "page": page,
                    "total_pages": t_pages
                })

            responses["data"] = data
        
    except Exception as e:
        _msg = str(e)
        # get CAUSE_MESSAGE of YouTubeTranscriptApi errors
        if "CAUSE_MESSAGE" in dir(e):
            cause = str(getattr(e, "CAUSE_MESSAGE"))
            # only for NoTranscriptFound error
            _msg = cause.split(":")[0] if ":" in cause else cause

        message = _msg
        responses["data"] = []

    return {
        "is_error": False if message == "" else True,
        # if there's no error, "message" contains only empty string
        "message": message,
        **responses
    }

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # this will take the last parameter if it's more than 1
        query_string = dict(parse_qsl(urlparse(self.path).query))

        responses = get(query_string)
        status_code = 200 if not responses["is_error"] else 400

        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        # convert python dict to json
        self.wfile.write(json.dumps(responses).encode())
        return