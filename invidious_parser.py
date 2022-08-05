#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup
import config

def add_playlist(text):
    playlistName = text.find("div", config.invidious_playlist_div).find("h3").decode_contents()
    tracks = text.findAll("div", config.invidious_vid_div)

    ret = []

    for track in tracks:
        title = track.find("p", "").decode_contents()
        artist = track.find("p", "channel-name").decode_contents()
        # TODO remove feat. ... from title to artists
        # TODO parse title for music videos (remove MV, feat, ..)
        url = track.find("div", "icon-buttons").find("a")['href'].replace("https://www.youtube.com/watch?v=", "").split("&", 1)[0]
        ret.append([playlistName, title, artist, url, "yt", url, ""])

    return ret


def add_vid(text):
    title_h1 = text.find("h1")
    title = title_h1.decode_contents().split("\n", 2)[1].strip()
    url = title_h1.find("a")['href'].replace("/watch?v=", "").split("&", 1)[0]
    artists = text.find("div", config.invidious_vid_link).find("span").decode_contents().split("<", 1)[0].strip()
    year = text.find("div", config.invidious_vid_date_div).find("p", id="published-date").find("b").decode_contents().split(" ")[-1]
    return [["", title, artists, url, "yt", url, year]]


def __search_yt(invInstance, search):
    req = requests.get(invInstance + "/api/v1/search", params={
        "q": search,
        "sort_by": "view_count",
        "duration": "short",
        "type": "video"})
    return json.loads(req.text)


def search_yt_id(invInstance, search, last=False):
    try:
        vids = __search_yt(invInstance, search)
        vidId = vids[0]['videoId']
    except IndexError:
        if last:
            return ""
        else:
            return search_yt_id(invInstance, search, True)
    return vidId
