# yt-transcripts

Go to [here](https://yt-transcripts.vercel.app/api) to see it live

Available parameters are:
- `v` - a Youtube video ID that will be used to find transcripts (example: `jNQXAC9IVRw`), this is __required__
- `list` - if it set to `true`, will return a list of transcripts available for a given video in `v`, other params will be ignored
- `lang` - language code to search for, multiple languages are also allowed (example: `es`, `ar`, `en,fr,ja`), if you are not sure, use `list` parameter to see available languages code, by default, this will look for English (`en`), if English not found, then first available language (alphabetically) will be used
- `tl` - if a language code is given, this will automatically translated into the requested language
- `type` - by default, this will look for manually created transcript then auto-generated transcript, but you can get only `manual` or `generated` transcripts using this parameter
- `key`- search and only returns text that contains the requested string, as opposed to returns all text in the transcript
- `cs` - set this parameter to `true` to make search case sensitive
- `marker` - string that used as a marker before and after `key` found in text, you can also use different markers for before and after `key` using `_%_`, for example `<mark>_%_</mark>`
- `size` - how much maximum text is returned, if not set, then return all text found
- `page` - the requested page based on the value of `size` parameter, if parameter `size` isn't exist, this will be ignored, page starts at 1