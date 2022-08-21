# music parser
> music-parser is a spotify, YouTube, Invidious and Piped parser that will take playlist and song links and parse them into a single SQLite database while trying to find a YouTube link to the song (using the Invidious). It can also download the songs to mp3 files using yt-dlp


## installation
GUI version:
`pip install -r requirements-gui.txt`

without GUI:
`pip install -r requirements.txt`

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
| `migrate_db(old_db, new_db)` | this will copy every entry from `old_db` to `new_db`
| `__replace_with_invidious(url)` | this will replace any YouTube or Piped `url` with a working Invidious one. This will not output any error if another `url` is given
| `add_manual_track(db_path, playlist_name, title, url, url_type, yt_link)` | this will add a new entry to the database without utilizing the internet
| `search_manual(db_path, search, what_to-search="title")` | this will search the given `search` term in the given database
| `renew_yt_link(db_path, rowid, yt_link="")` | this will either set the `yt_link` of the given `rowid` or output the top five results given by YouTube and let the user decide which one to pick
| `add_years(db_path)` | this will manually set all empty year rows but it needds a last.fm api key
| `update_metadata(db_path, download_path)` | this will update all metadata of the downloaded files 


## TODO
> What I might add in the future if I find the motivation

- move GUI in separate Thread to be able to search and use gui at the same time
- ability to parse artists and add them to a 'subscriptions' database
- ability to parse login to spotify and parse all subscribed playlists
- add unicode support
- add a cli and gui search option that is useable
- parse YouTube Video titles better (remove junk like: "M/V", "feat. ...", ...)
- change gui layout to something more useable
