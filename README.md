# music parser
> music-parser is a spotify, YouTube, Invidious and Piped parser that will take playlist and song links and parse them into a single SQLite database while trying to find a YouTube link to the song (either YouTube Music or Invidious). It can also download the songs to mp3 files using yt-dlp and create m3d playlists


## installation
GUI version:
`pip install -r requirements-gui.txt`

without GUI:
`pip install -r requirements.txt`

if there is any problem when downloading from youtube, try: `pip install -U yt-dlp`

if you install the project for the first time or parsing YouTube links takes too much time you should try manually renewing the `INVIDIOUS_MIRRORS` in `config.py` by setting them to the output of `renew_invidious_mirrors.py`

You may also need to install ffmpeg in order to convert the downloaded videos to mp3


## usage
`python music_parser.py <flags> url1 url2 url2 ...`

| flags | explanation | default value |
| -- | -- | -- |
| `-db <file>` | specify the sqlite database file location | `./db.db`
| `-d <path>` | download the urls to the specified path. If no urls are given this will download the whole database! | |
| `-gui` | open the gui version (`requirements-gui.txt` has to be installed) | |


## useful functions
> These are functions inside of music_parser.py Some of them are never called by the program but are useful when needing extendet functionality

| function name | explanation |
| -- | -- |
| `__get_invidious_instance()` | this will try to get an invidious instance that allows access to the invidious API
| `__replace_with_invidious(url)` | this will replace any YouTube or Piped `url` with a working Invidious one. This will not output any error if another `url` is given
| `add_manual_track(db_path, playlists, title, genre, url, url_type, yt_link, dir)` | this will add a new entry to the database without utilizing the internet
| `search_manual(db_path, search, what_to-search="title")` | this will search the given `search` term in the given database
| `renew_yt_link(db_path, rowid, yt_link="")` | this will either set the `yt_link` of the given `rowid` or output the top five results given by YouTube and let the user decide which one to pick
| `update_metadata(db_path, download_path)` | this will update all metadata of the downloaded files 


## TODO
> What I might add in the future if I find the motivation

- move GUI in separate Thread to be able to search and use gui at the same time
- change to dark theme
- ability to subscribe to artists
- ability to login to spotify and parse all subscribed playlists
- fix unicode characters when parsing titles, ...
- add a cli search options
