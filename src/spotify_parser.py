#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup


def add_playlist(text, trackDIV, trackLINK, artistSPAN):
    playlistName = text.title.decode_contents()[:text.title.decode_contents().rfind(" - ")]
    tracks = text.findAll("div", trackDIV)
    ret = []

    for track in tracks:
        title = track.find("a", trackLINK)
        artists = track.find("span", artistSPAN).findAll("a")
        artist_arr = []

        for artist in artists:
            artist_arr.append(artist.decode_contents())
        ret.append([playlistName, title.decode_contents(), ",".join(str(x) for x in artist_arr), title['href'][title['href'].index("track/") + 6:], "spotify", ""])
    return ret


def add_track(text, url):
    title = text.title.decode_contents()[:text.title.decode_contents().rfind(" - ")]
    artists = text.title.decode_contents()[text.title.decode_contents().rfind(" - ") + 8 :text.title.decode_contents().rfind(" | ")]
    url = url[url.index("track/") + 6:]

    return [["", title, artists, url, "spotify", ""]]
