#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import config


# TODO add function/ new file to get all playlists from user (with and without login)

def add_playlist(text):
    playlistName = text.title.decode_contents()[:text.title.decode_contents().rfind(" - ")]
    tracks = text.findAll("div", config.spotify_track_div)
    ret = []
    try:
        year = text.find("meta", property="music:release_date")["content"].split("-")[0]
    except:
        year = ""

    for track in tracks:
        title = track.find("a", config.spotify_track_link)
        artists = track.find("span", config.spotify_artists_span).findAll("a")
        artist_arr = []

        for artist in artists:
            artist_arr.append(artist.decode_contents())

        ret.append([playlistName, title.decode_contents(), ",".join(str(x) for x in artist_arr), title['href'][title['href'].index("track/") + 6:], "spotify", "", year])
    return ret


def add_track(text, url):
    title = text.title.decode_contents()[:text.title.decode_contents().rfind(" - ")]
    artists = text.title.decode_contents()[text.title.decode_contents().rfind(" - ") + 8 :text.title.decode_contents().rfind(" | ")]
    url = url[url.index("track/") + 6:]
    year = text.find("meta", property="music:release_date")["content"].split("-")[0]

    return [["", title, artists, url, "spotify", "", year]]
