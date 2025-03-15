import music_struct
import re

from invidious_parser import __fix_yt_title, __fix_yt_artist

def add_playlist(text):
    print_error("NOT IMPLEMENTED")
    return None

def add_vid(text):
    title = __fix_yt_title(text.title.decode_contents().replace(" - YouTube", ""))
    url = re.sub(".*/watch\\?v=", "", text.find("link", rel="canonical")["href"]).split("&", 1)[0]
    artists = __fix_yt_artist(text.find("link", itemprop="name")["content"])
    year = text.find("meta", itemprop="datePublished")["content"][0:4]
    return [
        music_struct.song(
            title=title, artists=artists, url=url, url_type="yt", yt_link=url, year=year
        )
    ]
