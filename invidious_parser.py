#!/usr/bin/env python3

import requests
import json
import re
import config
import music_struct


def __fix_yt_title(title):
    if not config.fix_yt_title_artist:
        return title
    q = re.search("(^| )(‘.*’|'.*'|\".*\")", title)
    if q:
        title = q.group(2)
    else:
        title = re.sub("\(.*\)", "", title)
        title = re.sub("\[.*\]", "", title)

        dash = re.search(" - ", title)
        if dash:
            ntitle = title[dash.span()[1] :].strip()
            if ntitle != "":
                title = ntitle

        feat = re.search(" (ft|feat|featuring)\.? ", title.lower())
        if feat:
            ntitle = title[0 : feat.span()[0]].strip()
            if ntitle != "":
                title = ntitle

        mv = re.search(" ?M\/?V ?", title)
        if mv:
            title = title[0 : mv.span()[0]] + title[mv.span()[1] :]

        if " | " in title:
            title = title.split(" | ")[0]

    return title.strip()


def __fix_yt_artist(artist):
    if not config.fix_yt_title_artist:
        return artist
    elif "VEVO" in artist:
        artist = artist.replace("VEVO", "")
        return re.sub(r"([A-Z])", r" \1", artist)
    else:
        return artist.replace(" - Topic", "")


def add_playlist(text):
    playlistName = (
        text.find("div", config.invidious_playlist_div).find("h3").decode_contents()
    )
    tracks = text.findAll("div", config.invidious_vid_div)

    ret = []

    for track in tracks:
        title = __fix_yt_title(track.find("p", "").decode_contents())
        artist = __fix_yt_artist(track.find("p", "channel-name").decode_contents())
        # TODO remove feat. ... from title to artists
        # TODO parse title for music videos (remove MV, feat, ..)
        url = (
            track.find("div", "icon-buttons")
            .find("a")["href"]
            .replace("https://www.youtube.com/watch?v=", "")
            .split("&", 1)[0]
        )
        ret.append(
            music_struct.song(
                title=title,
                playlists=playlistName,
                artists=artist,
                url=url,
                url_type="yt",
                yt_link=url,
                dir=playlistName,
            )
        )

    return ret


def add_vid(text):
    title_h1 = text.find("h1")
    title = __fix_yt_title(title_h1.decode_contents().split("\n", 2)[1].strip())
    url = title_h1.find("a")["href"].replace("/watch?v=", "").split("&", 1)[0]
    artists = __fix_yt_artist(
        text.find("div", config.invidious_vid_link)
        .find("span")
        .decode_contents()
        .split("<", 1)[0]
        .strip()
    )
    year = (
        text.find("div", config.invidious_vid_date_div)
        .find("p", id="published-date")
        .find("b")
        .decode_contents()
        .split(" ")[-1]
    )
    return [
        music_struct.song(
            title=title, artists=artists, url=url, url_type="yt", yt_link=url, year=year
        )
    ]


def __search_yt(invInstance, search):
    req = requests.get(
        invInstance + "/api/v1/search",
        params={
            "q": search,
            "sort_by": "view_count",
            "duration": "short",
            "type": "video",
        },
    )
    return json.loads(req.text)


def search_yt_id(invInstance, search, last=False):
    try:
        vids = __search_yt(invInstance, search)
        vidId = vids[0]["videoId"]
    except IndexError:
        if last:
            return ""
        else:
            return search_yt_id(invInstance, search, True)
    return vidId
