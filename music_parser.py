#!/usr/bin/env python3

import os
import sys
import subprocess
import json
import requests
from bs4 import BeautifulSoup
import sqlite3
import eyed3
import random
from queue import Queue
from threading import Thread
from ytmusicapi import YTMusic

import config
import spotify_parser
import invidious_parser
import youtube_music_parser
import SQLite_GUI


# The following classes are copied from: https://betterprogramming.pub/how-to-make-parallel-async-http-requests-in-python-d0bd74780b8a
class Worker(Thread):

    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                print(e)
            finally:
                self.tasks.task_done()


class ThreadPool:
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        self.tasks.put((func, args, kargs))

    def map(self, func, args_list):
        for args in args_list:
            self.add_task(func, args)

    def wait_completion(self):
        self.tasks.join()


def print_error(text):
    print(f"\033[0;31mERROR: {text}\033[1;0m")


def print_success(text):
    print(f"\033[0;32mSUCCESS: {text}\033[1;0m")


__current_invidious_instance = ""
__current_invidious_counter = 0
ytmusic = None


def __get_invidious_instance(i=3):
    global __current_invidious_instance
    global __current_invidious_counter
    if __current_invidious_counter == 0:
        __current_invidious_counter = 10
        __current_invidious_instance = config.INVIDIOUS_MIRRORS[random.randint(0, len(config.INVIDIOUS_MIRRORS) - 1)]
        try:
            res = requests.get(__current_invidious_instance)
        except:
            if i <= 0:
                print_error("Please check your internet connection")
                return None
            return __get_invidious_instance(i - 1)


        if res.status_code != 200:
            if i <= 0:
                print_error("couldn't connect to an Invidious instance.\nCheck your internet connection or update the config.py file")
                return None
            return __get_invidious_instance(i - 1)
    else:
        __current_invidious_counter -= 1
    return __current_invidious_instance


def __get_ytmusic():
    global ytmusic
    if not ytmusic:
        ytmusic = YTMusic()
    return ytmusic


def migrate_db(old_db_path, new_db_path):
    oCon = sqlite3.connect(old_db_path)
    oDb = oCon.cursor()
    nCon = sqlite3.connect(old_db_path)
    nDb = nCon.cursor()

    nDb.execute('''CREATE TABLE IF NOT EXISTS playlists
            (playlist_name TEXT, title TEXT NOT NULL, artists TEXT, url TEXT, url_type TEXT, yt_link TEXT, year INTEGER)''')

    data_arr = oDb.execute("SELECT (playlist_name, title, artists, url, url_type, yt_link) FROM playlists").fetchall()
    nDb.close()

    for data in data_arr:
        nDb.execute("INSERT INTO playlists (playlist_name, title, artists, url, url_type, yt_link, year) VALUES (\'" + "\',\'".join(x.replace("'", "’") for x in data) + "\')")
    nDb.commit()
    oDb.close()


def parse_urls(output_file, urls, download_files=False):
    pool = ThreadPool(40)
    try:
        con = sqlite3.connect(output_file)
        db = con.cursor()
        db.execute('''CREATE TABLE IF NOT EXISTS playlists
            (playlist_name TEXT, title TEXT, artists TEXT, url TEXT, url_type TEXT, yt_link TEXT, year INTEGER)''')
    except:
        print_error("cannot parse " + output_file)
        return "cannot parse " + output_file

    # if url is empty, and download_path is given -> download the whole database
    if download_files and len(urls) == 0:
        data_arr = db.execute("SELECT * FROM playlists").fetchall()
        down_arr = []
        for data in data_arr:
            down_arr.append([data[5], data[1], data[0], data[2], data[6]])
        pool.map(downloadVideo, down_arr)
    else:
        arr = []
        for url in urls:
            arr.append([url, output_file, pool, download_files])

        pool.map(__parse_single_url, arr)

    pool.wait_completion()
    con.close()
    return ""


def __replace_with_invidious(url):
    invInstance = __get_invidious_instance()
    if invInstance is not None:
        if "://" not in url:
            return invInstance + "/" + url
        else:
            return invInstance + "/" + url.replace("://", "").split("/")[1]
    else:
        return None


def __get_url_data(url):
    # check if link is to youtube and replace it with an invidious instance
    if "www.youtube.com" in url or "youtu.be" in url or "://" not in url:
        url = __replace_with_invidious(url)

    try:
        req = requests.get(url)
    except:
        return None

    # check if request was succesfull
    if not req.status_code == 200:
        return None

    soup = BeautifulSoup(req.text, "html.parser")

    # create database table if it doesn't exist
    try:
        site_name = soup.find("title").decode_contents().rsplit(None, 1)[-1]
    except:
        return None

    if site_name == "Spotify" or site_name == "Playlist":
        site_about = soup.find("meta", property="og:type")["content"]
        if site_about == "music.playlist" or site_about == "music.album":
            arr = spotify_parser.add_playlist(soup)
        elif site_about == "music.song":
            arr = spotify_parser.add_track(soup, url)
        # TODO add artists
        else:
            print_error(f"cannot_parse {site_name}: {site_about.replace('spotify.', '')}")
            return None
        return arr
    elif site_name == "Piped":
        return __get_url_data(__replace_with_invidious(url))
    elif site_name == "Invidious":
        # TODO add channels
        if "playlist" in url:
            return invidious_parser.add_playlist(soup)
        else:
            return invidious_parser.add_vid(soup)
    else:
        print_error("cannot parse " + site_name)
        return None


def __update_file_metadata(playlist, title, artists, year):
        path = f"{playlist}/{title.replace('/', '|')}.mp3" if playlist and playlist != "./" else f"unsorted/{title.replace('/', '|')}.mp3"
        if title != "" and os.path.exists(path):
            file = eyed3.load(path)
            file.tag.album = playlist
            file.tag.title = title
            file.tag.artist = artists
            file.tag.original_release_date = year
            file.tag.save()
        else:
            print_error(f"{path} does not exist")


def update_metadata(db_path, download_path):
    con = sqlite3.connect(db_path)
    db = con.cursor()
    os.chdir(download_path)
    arr = db.execute("SELECT playlist_name,title,artists,year FROM playlists").fetchall()
    for data in arr:
        __update_file_metadata(data[0], data[1], data[2], data[3])
    con.commit()
    con.close()


def add_manual_track(db_path, playlist_name, title, artists, url, url_type, yt_link, year):
    con = sqlite3.connect(db_path)
    db = con.cursor()
    __add_to_db([playlist_name, title, artists, url, url_type, yt_link, year])
    con.commit()
    con.close()


def __search_db(db_cursor, search, what_to_search):
    return db_cursor.execute(f"SELECT rowid, * FROM playlists WHERE {what_to_search} LIKE '{search}'").fetchall()


def search_manual(db_path, search, what_to_search="title"):
    if what_to_search == "playlist":
        what_to_search = "playlist_name"
    elif what_to_search == "artist":
        what_to_search = "artists"

    con = sqlite3.connect(db_path)
    db = con.cursor()
    try:
        result = __search_db(db, search, what_to_search)
    except:
        print_error(f"{what_to_search} doesn't exist.")

    for res in result:
        print(",".join(res))

    con.commit()
    con.close()


def __add_year(arr):
    rowid = arr[1]
    title = arr[2]
    artists = arr[3]

    year = ""

    if artists:
        artists = artists.split(",")
        for artist in artists:
            res = requests.get(f"{config.lastfm_root}?method=track.getInfo&track={title}&artist={artist}&api_key={config.lastfm_api_key}&format=json")
            try:
                year = (json.loads(res.text))["track"]["wiki"]["published"].split(" ")[2].replace(",","")
                if year:
                    print_success(f"Found the year {year} for {title}")
                    break
            except:
                pass

    else:
        res = requests.get(f"{config.lastfm_root}?method=track.getInfo&track={title}&api_key={config.lastfm_api_key}&format=json")
        try:
            year = (json.loads(res.text))["track"]["wiki"]["published"].split(" ")[2].replace(",","")
        except:
            pass

    if year:
        con = sqlite3.connect(arr[0])
        db_cursor = con.cursor()
        db_cursor.execute(f"UPDATE playlists SET year='{year}' WHERE rowid={rowid}")
        con.commit()
        con.close()
        # print_success(f"Found the year {year} for {title}")
    else:
        # print_error(f"Didn't find a year for {title}")
        pass


def __get_new_yt_links(title, artist):
    if config.use_invidious:
        return invidious_parser.__search_yt(__get_invidious_instance(), f"{title} {artist} music video")
    else:
        return youtube_music_parser.__search_yt(__get_ytmusic(), f"{title} {artist}")


def renew_yt_link(db_path, id, yt_link=""):
    con = sqlite3.connect(db_path)
    db = con.cursor()
    if yt_link == "":
        db.execute(f"UPDATE playlists SET yt_link='{yt_link}' WHERE rowid={id}")
    else:
        data = db.execute(f"SELECT title FROM playlists WHERE rowid={id}")
        try:
            res = __get_new_yt_links(data[2], data[3])
            for i in range(5):
                print(f"({i + 1}) '{res[i]['title']} by '{res[i]['author']} : {res[i]['videoId']}")
            i = input("\ninput the id: ")
            if i != "":
                db.execute(f"UPDATE playlists SET yt_link='{res[int(i - 1)]['videoId']}' WHERE rowid={id}")

        except:
            print_error("couldn't parse YouTube links")

    con.commit()
    con.close()


def __add_to_db(db_cursor, data):
    db_cursor.execute("INSERT INTO playlists (playlist_name, title, artists, url, url_type, yt_link, year) VALUES (\'" + "\',\'".join(x.replace("'", "’") for x in data) + "\')")


def __parse_single_url(arr):
    url = arr[0]
    con = sqlite3.connect(arr[1])
    db = con.cursor()
    pool = arr[2]
    download_files = arr[3]

    data_arr = __get_url_data(url)

    if data_arr is not None and len(data_arr) != 0:
        if download_files:
            exit()
            down_arr = []
            for data in data_arr:
                down_arr.append([data[5].replace("'", "’"), data[1].replace("'", "’"), data[0], data[2], data[6]])
            pool.map(downloadVideo, down_arr)

        fail_counter = 0
        for data in data_arr:
            if len(db.execute("SELECT title FROM playlists WHERE playlist_name='" + data[0].replace("'", "’") + "' AND title='" + data[1].replace("'", "’") + "'").fetchall()) < 1:
                try:
                    if data[5] == "":
                        if config.use_invidious:
                            data[5] = invidious_parser.search_yt_id(__get_invidious_instance(), data[2].replace("'", "’") + " " + data[1].replace("'", "’") + " music video")
                        else:
                            data[5] = youtube_music_parser.search_yt_id(__get_ytmusic(), data[2].replace("'", "’") + " " + data[1].replace("'", "’"))
                except:
                    data[5] = ""
                try:
                    __add_to_db(db, data)
                except:
                    fail_counter += 1
                    pass
        con.commit()
        con.close()

        if fail_counter == len(data_arr):
            print_error(f"couldn't save {url}")
        elif fail_counter > 0:
            print_error(f"only saved {len(data_arr) - fail_counter} out of {len(data_arr)} from {url}")
        else:
            print_success(f"parsed {url}")

    else:
        print_error(f"couldn't parse {url}")


def __get_proxy():
    proxy = proxy_file.readline()
    if proxy:
        return proxy.strip()
    else:
        proxy_file.seek(0)
        return __get_proxy()


def downloadVideo(arr):
    youtube_id = arr[0]
    file_name = arr[1].replace("/", "|")
    playlist = arr[2]
    artists = arr[3]
    year = arr[4]

    if youtube_id == "":
        return

    if playlist == "" or playlist == "./":
        playlist = "unsorted"
    try:
        os.mkdir(playlist.replace("'", "’"))
    except:
        pass
    folder = playlist.replace("'", "’") + "/"

    # TODO proxy this
    if not os.path.exists(f"{folder}{file_name}.mp3"):
        if config.proxy_file != "":
            subprocess.call(f"yt-dlp https://www.youtube.com/watch?v={youtube_id} -x --sponsorblock-remove all -o '{folder}{file_name}.%(ext)s' --audio-format mp3 --proxy {__get_proxy()}", shell=True)
        else:
            subprocess.call(f"yt-dlp https://www.youtube.com/watch?v={youtube_id} -x --sponsorblock-remove all -o '{folder}{file_name}.%(ext)s' --audio-format mp3", shell=True)
        __update_file_metadata(playlist, file_name, artists, year)


if __name__ == '__main__':
    i = 1
    urls = []
    output_file = "db.db"
    download_path = ""
    useGui = False
    while i < len(sys.argv):
        if sys.argv[i] == "-db":
            output_file = sys.argv[i + 1]
            i += 1
        elif sys.argv[i] == "-d":
            try:
                download_path = sys.argv[i + 1]
            except IndexError:
                download_path = "."
            i += 1
        elif sys.argv[i] == "-gui":
            useGui = True
        elif sys.argv[i][0] == "-":
            print_error(f"'{sys.argv[i]}' is not a valid argument")
            exit()
        else:
            urls.append(sys.argv[i])
        i += 1

    if download_path == ".":
        path = output_file.split("/")
        path.pop(-1)
        if len(path) > 0:
            os.chdir("/".join(path))
    elif download_path != "":
        os.chdir(download_path)

    if config.proxy_file != "":
        proxy_file = open(config.proxy_file, 'r')

    if useGui:
        SQLite_GUI.main(output_file, urls)
    else:
        parse_urls(output_file, urls, download_path != "")

    if config.proxy_file != "":
        proxy_file.close()
