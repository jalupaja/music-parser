#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup

def add_playlist(text, vidDiv, vidLink):
    playlistName = text.find("div", "pure-u-2-3").find("h3").decode_contents()
    tracks = text.findAll("div", vidDiv)

    ret = []

    for track in tracks:
        title = track.find("p", "").decode_contents()
        artist = track.find("p", "channel-name").decode_contents()
        # TODO add feat. ... from title to artists
        # TODO parse title for music videos (remove MV, feat, ..)
        url = track.find("div", "icon-buttons").find("a")['href'].replace("https://www.youtube.com/watch?v=", "").split("&", 1)[0]
        ret.append([playlistName, title, artist, url, "yt", url])

    return ret


def add_vid(text, vidLink):
    title_h1 = text.find("h1")
    title = title_h1.decode_contents().split("\n", 2)[1].strip()
    url = title_h1.find("a")['href'].replace("/watch?v=", "").split("&", 1)[0]
    artists = text.find("div", vidLink).find("span").decode_contents().split("<", 1)[0].strip()
    return [["", title, artists, url, "yt", url]]


def search_yt_id(invInstance, search, last=False):
    req = requests.get(invInstance + "/api/v1/search", params={
        "q": search,
        "duration": "short",
        "type": "video"})
    try:
        vids = json.loads(req.text)
        vidId = vids[0]['videoId']
    except IndexError:
        if last:
            return ""
        else:
            return search_yt_id(invInstance, search, True)
    return vidId
