#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup


def add_playlist(text, trackDIV, trackLINK, artistSPAN):
    playlistName = text.title.decode_contents()[:text.title.decode_contents().rfind(" - ")]
    tracks = text.findAll("div", trackDIV)
    ret = []

    for track in tracks:
        span1 = track.find("a", trackLINK)
        span2 = track.find("span", artistSPAN).findAll("a")
        artists = []

        for artist in span2:
            artists.append(artist.decode_contents())
        ret.append([playlistName, span1.decode_contents(), ",".join(str(x) for x in artists), span1['href'][span1['href'].index("track/") + 6:], "spotify"])
    return ret


def add_track(text, url):
    title = text.title.decode_contents()[:text.title.decode_contents().rfind(" - ")]
    artists = text.title.decode_contents()[text.title.decode_contents().rfind(" - ") + 8 :text.title.decode_contents().rfind(" | ")]
    url = url[url.index("track/") + 6:]

    return [["", title, artists, url, "spotify"]]
