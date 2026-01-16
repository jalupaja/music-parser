#!/usr/bin/env python3

import re

class song:
    def __init__(
        self,
        title=None,
        select_data=None,
        playlists="",
        artists="",
        genre="",
        url="",
        url_type="",
        yt_link="",
        year="",
        dir="",
        filetype="",
    ):
        if title is None and select_data is None:
            raise Exception("either title or select_data must be explicitly specified")
        elif title is not None:
            self.set_title(title)
            self.set_playlists(playlists)
            self.set_artists(artists)
            self.set_genre(genre)
            self.set_url(url)
            self.set_url_type(url_type)
            self.set_yt_link(yt_link)
            self.set_year(year)
            self.set_dir(dir)
            self.set_filetype(filetype)
        else:
            # rowid is only needed in specific cases:
            if len(select_data) >= 11:
                self.set_rowid(select_data[0])
                self.set_playlists(select_data[1])
                self.set_title(select_data[2])
                self.set_artists(select_data[3])
                self.set_genre(select_data[4])
                self.set_url(select_data[5])
                self.set_url_type(select_data[6])
                self.set_yt_link(select_data[7])
                self.set_year(select_data[8])
                self.set_dir(select_data[9])
                self.set_filetype(select_data[10])
            else:
                self.set_playlists(select_data[0])
                self.set_title(select_data[1])
                self.set_artists(select_data[2])
                self.set_genre(select_data[3])
                self.set_url(select_data[4])
                self.set_url_type(select_data[5])
                self.set_yt_link(select_data[6])
                self.set_year(select_data[7])
                self.set_dir(select_data[8])
                self.set_filetype(select_data[9])

    def set_rowid(self, rowid):
        self.rowid = rowid
    def set_title(self, title):
        self.title = title
    def set_playlists(self, playlists):
        self.playlists = playlists
    def set_artists(self, artists):
        self.artists = artists
    def set_genre(self, genre):
        self.genre = genre
    def set_url(self, url):
        self.url = url
    def set_url_type(self, url_type):
        self.url_type = url_type
    def set_yt_link(self, yt_link):
        self.yt_link = yt_link
    def set_year(self, year):
        self.year = year
    def set_dir(self, dir):
        if dir == "":
            dir = "unsorted"
        self.dir = dir
    def set_filetype(self, filetype):
        # Fallback to mp3
        if filetype == "":
            filetype = "mp3"
        self.filetype = filetype

    def __filesystem_save(self, path):
        invalid_chars = r'[<>:"/\\|?*\'’\"() ]' # for windows and linux
        new_path = re.sub(invalid_chars, '_', path)

        # Umlaute
        new_path = new_path.replace('ä', 'ae').replace('Ä', 'Ae')
        new_path = new_path.replace('ö', 'oe').replace('Ö', 'Oe')
        new_path = new_path.replace('ü', 'ue').replace('Ü', 'Ue')
        new_path = new_path.replace('ß', 'ss').replace('ẞ', 'Ss')

        return new_path

    def at(self, at):
        match at:
            case "title":
                return self.title
            case "playlists":
                return self.playlists
            case "artists":
                return self.artists
            case "genre":
                return self.genre
            case "url":
                return self.url
            case "url_type":
                return self.url_type
            case "yt_link":
                return self.yt_link
            case "year":
                return self.year
            case "dir":
                return self.dir
            case "filetype":
                return self.filetype
            case _:
                return None

    def path(self, dir=None, title=None, filetype=None):
        # update possible changes
        if dir is None:
            dir = self.dir
        if dir == "":
            dir = "unsorted"
        if title is None:
            title = self.title
        if filetype is None:
            filetype = self.filetype

        title = self.__filesystem_save(title)

        return f"{dir}/{title}.{filetype}"


    def get_values(self):
        return [
            self.playlists,
            self.title,
            self.artists,
            self.genre,
            self.url,
            self.url_type,
            self.yt_link,
            self.year,
            self.dir,
            self.filetype,
        ]


    def get_sql_values(self):
        values = self.get_values()

        values = [v.replace("'", "''") for v in values]
        return values


    def __str__(self):
        return str(self.get_values())


sql_columns = "playlists, title, artists, genre, url, url_type, yt_link, year, dir, filetype"
sql_table = "playlists TEXT, title TEXT NOT NULL, artists TEXT NOT NULL, genre TEXT NOT NULL, url TEXT NOT NULL, url_type TEXT NOT NULL, yt_link TEXT NOT NULL, year INTEGER NOT NULL, dir TEXT NOT NULL, filetype TEXT NOT NULL"
