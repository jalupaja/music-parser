import music_struct
import re

def fix_yt_title(title):
    if not config.fix_yt_title_artist:
        return title
    q = re.search("(^| )(‘.*’|'.*'|\".*\")", title)
    if q:
        title = q.group(2)
    else:
        title = re.sub('\\(.*\\)', "", title)
        title = re.sub('\\[.*\\]', "", title)

        dash = re.search(" - ", title)
        if dash:
            ntitle = title[dash.span()[1] :].strip()
            if ntitle != "":
                title = ntitle

        feat = re.search(" (ft|feat|featuring)\\.? ", title.lower())
        if feat:
            ntitle = title[0 : feat.span()[0]].strip()
            if ntitle != "":
                title = ntitle

        mv = re.search(" ?M\\/?V ?", title)
        if mv:
            title = title[0 : mv.span()[0]] + title[mv.span()[1] :]

        if " | " in title:
            title = title.split(" | ")[0]

    return title.strip()


def fix_yt_artist(artist):
    if not config.fix_yt_title_artist:
        res = artist
    elif "VEVO" in artist:
        artist = artist.replace("VEVO", "")
        res = re.sub(r"([A-Z])", r" \1", artist)
    else:
        res = artist.replace(" - Topic", "")

    return res.strip()


def add_playlist(text):
    print_error("NOT IMPLEMENTED")
    return None

def add_vid(text):
    print("yt: add_vid")
    title = fix_yt_title(text.title.decode_contents().replace(" - YouTube", ""))
    url = re.sub(".*/watch\\?v=", "", text.find("link", rel="canonical")["href"]).split("&", 1)[0]
    artists = fix_yt_artist(text.find("link", itemprop="name")["content"])
    year = text.find("meta", itemprop="datePublished")["content"][0:4]
    return [
        music_struct.song(
            title=title, artists=artists, url=url, url_type="yt", yt_link=url, year=year
        )
    ]
