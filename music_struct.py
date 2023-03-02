#!/usr/bin/env python3

class song:
    def __init__(self, title, playlists="", artists="", genre="", url="", url_type="", yt_link="", year="", dir=""):
        self.title = title
        self.playlists = playlists
        self.artists = artists
        self.genre = genre
        self.url = url
        self.url_type = url_type
        self.yt_link = yt_link
        self.year = year
        self.dir = dir

    def from_select(self, data):
        self.playlists = data[0]
        self.title = data[1]
        self.artists = data[2]
        self.genre = data[3]
        self.url = data[4]
        self.url_type = data[5]
        self.yt_link = data[6]
        self.year = data[7]
        self.dir = data[8]
        return self

    def get_sql_collunms(self):
        return "playlists, title, artists, genre, url, url_type, yt_link, year, dir"

    def get_values(self):
        return [self.playlists.replace('\'', '’'), self.title.replace('\'', '’'), self.artists.replace('\'', '’'), self.genre.replace('\'', '’'), self.url.replace('\'', '’'), self.url_type.replace('\'', '’'), self.yt_link.replace('\'', '’'), self.year.replace('\'', '’'), self.dir.replace('\'', '’')]


sql_table = "playlists TEXT, title TEXT NOT NULL, artists TEXT, genre TEXT, url TEXT, url_type TEXT, yt_link TEXT, year INTEGER, dir TEXT"
