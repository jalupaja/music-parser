#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import spotify_parser
import sqlite3
import json


def err_file(file):
    print("ERROR: cannot access " + file)


def err_parse(site, extra):
    if extra == "":
        print("ERROR: cannot parse " + site)
    else:
        print("ERROR: cannot parse " + site + ": " + extra)


def __setup_output(outputVar, outputFile):
    if outputVar == "sqlite" or outputVar == "sqlite3":
        con = sqlite3.connect(outputFile)
        con.cursor().execute('''CREATE TABLE IF NOT EXISTS playlists
            (playlist_name TEXT, title TEXT, artists TEXT, url TEXT, url_type TEXT, youtube_url TEXT)''')
        con.close()
        return __array_to_sqlite
    elif outputVar == "json":
        with open(outputFile, 'w') as file:
            file.write("")
        return __array_to_json


def __array_to_sqlite(outputFile, arr):
    conn = sqlite3.connect(outputFile)
    db = conn.cursor()
    for data in arr:
        db.execute("INSERT INTO playlists (playlist_name, title, artists, url, url_type) VALUES (\'" + "\',\'".join(x.replace("'", "") for x in data) + "\')")
    conn.close()


def __array_to_json(outputFile, arr):

    if len(arr) == 0:
        return
    out = []
    tracks = []
    plName = arr[0][0]
    for data in arr:
        if data[0] == plName:
            tracks.append({"title": data[1], "artists": data[2], "url": data[3], "url_type": data[4]})
        else:
            out.append({"name": plName, "tracks": tracks})
            plName = data[0]
            tracks.clear()
            tracks.append({"title": data[1], "artists": data[2], "url": data[3], "url_type": data[4]})

    out.append({"name": plName, "tracks": tracks})
    tracks.append({"title": data[1], "artists": data[2], "url": data[3], "url_type": data[4]})

    with open(outputFile, 'w') as file:
        file.write(json.dumps(out))


def __parse_single_url(url):
    # parse from local file
    # with open("T/spotify_parser/playlist/movie_playlist.html") as fp:
    with open("T/spotify_parser/album/album.html") as fp:
    # with open("T/spotify_parser/track/track.html") as fp:
        soup = BeautifulSoup(fp, features="html.parser")
    url = "album/abc"

    # parse from url
    # req = requests.get(url)
    # soup = BeautifulSoup(req.text, "html.parser")
    # TODO check if request was succesfull

    # create database table if it doesn't exist
    site_name = soup.find("meta", property="og:site_name")["content"]

    if site_name == "Spotify":
        site_about = soup.find("meta", property="og:type")["content"]
        if site_about == "music.playlist" or site_about == "music.album":
            return spotify_parser.add_playlist(soup, "Row__Container-sc-brbqzp-0 jKreJT", "EntityRowV2__Link-sc-ayafop-8 cGmPqp", "Type__StyledComponent-sc-1ell6iv-0 bhCKIk Mesto-sc-1e7huob-0 Row__Subtitle-sc-brbqzp-1 hTPACX gmIWQx")
        elif site_about == "music.song":
            return spotify_parser.add_track(soup, url)
        else:
            err_parse(site_name, site_about.replace("spotify.", ""))
            return None
    else:
        err_parse(site_name)
        return None


def parse_urls(url, outputVar, outputFile):

    urls = url

    try:
        output_func = __setup_output(outputVar, outputFile)
    except:
        err_file(outputFile)

    if isinstance(url, str):
        urls = [url]

    data = []

    for uri in urls:
        add = __parse_single_url(uri)
        if add is not None:
            data.append(add)

    output_func(outputFile, data)
