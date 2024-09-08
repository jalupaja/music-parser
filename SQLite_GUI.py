#!/usr/bin/env python3

# This file is originally from https://github.com/jalupaja/SQLite-gui
# and has been edited to add some functionality to this project

from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QRadioButton,
    QTextEdit,
    QPlainTextEdit,
    QLabel,
    QPushButton,
    QMessageBox,
    QInputDialog,
    QComboBox,
    QGroupBox,
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSlot, Qt
import taglib
import os
import sys
import sqlite3

import music_parser
import music_struct
from music_struct import song
import config


def print_error(text):
    print("\033[0;31mERROR: " + text + "\033[1;0m")


class TableView(QTableWidget):
    def __init__(self, *args):
        QTableWidget.__init__(self, *args)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.cellChanged.connect(cellChanged)


def search(search):
    if search == "":
        for row in range(qTable.rowCount()):
            qTable.setRowHidden(row, False)
    else:
        items = qTable.findItems(search, Qt.MatchFlag.MatchRegularExpression)
        searched_rows = []
        for i in items:
            try:
                searched_rows.append(i.row())
            except:
                pass
        for row in range(qTable.rowCount()):
            qTable.setRowHidden(row, row not in searched_rows)


def __update_search():
    search(txt_search.toPlainText())


def __get_selected_table():
    return box_tables.currentText()


def tablesChanged():
    previous_table = __get_selected_table()
    try:
        box_tables.currentIndexChanged.disconnect()
    except TypeError:
        pass

    box_tables.clear()

    tables = db_execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    select_index = 0
    i = 0
    for table in tables:
        box_tables.addItem(table[0])
        if table[0] == previous_table:
            select_index = i
        else:
            i += 1

        box_tables.setCurrentIndex(select_index)
        box_tables.currentIndexChanged.connect(tableButtonsChanged)


def tableButtonsChanged():
    global qTable

    selected_table = __get_selected_table()

    global renewing_table
    renewing_table = True

    qTable.clear()
    data = db_execute(f"SELECT rowid,* FROM '{selected_table}'")
    cols = data.description
    rows = data.fetchall()

    colLen = 1
    headers = []
    rowid_changed = 0
    for i in range(len(cols)):
        if cols[i][0] in headers:
            headers.pop(0)
            rowid_changed = 1
        else:
            colLen += 1
        headers.append(cols[i][0])
    headers.append(" ")

    qTable.setColumnCount(colLen)
    qTable.setRowCount(len(rows))
    qTable.setHorizontalHeaderLabels(headers)

    qTable.sortByColumn(0, Qt.SortOrder.AscendingOrder)
    rowLen = len(rows)
    if rowLen:
        for rowCount in range(rowLen):
            for colCount in range(colLen):
                if colCount + 1 == colLen:
                    btn_del = QPushButton("x", qTable)
                    btn_del.clicked.connect(btn_push_del)
                    qTable.setCellWidget(rowCount, colCount, btn_del)
                else:
                    nItem = QTableWidgetItem()
                    nItem.setData(
                        Qt.ItemDataRole.DisplayRole,
                        rows[rowCount][colCount + rowid_changed],
                    )
                    qTable.setItem(rowCount, colCount, nItem)
                    if colCount == 0:
                        nItem.setFlags(nItem.flags() & Qt.ItemFlag.ItemIsEditable)
            rowCount += 1
    renewing_table = False
    __update_search()


def __pathify_playlist(playlist):
    return f"../{playlist}\n"


def __update_playlist(playlist_file, old_path="", new_path=""):
    try:
        os.mkdir("playlists")
    except FileExistsError:
        pass

    try:
        with open(playlist_file, "r", encoding="utf-8") as file_read:
            lines = file_read.readlines()
    except FileNotFoundError:
        lines = []

    if old_path and not new_path:
        # remove
        try:
            lines.remove(__pathify_playlist(old_path))
        except ValueError:
            pass
    elif old_path and new_path:
        # replace
        try:
            idx = lines.index(__pathify_playlist(old_path))
            lines[idx] = __pathify_playlist(new_path)
        except ValueError:
            lines.append(__pathify_playlist(new_path))
    elif not old_path and new_path:
        # append
        lines.append(__pathify_playlist(new_path))

    if len(lines) < 1:
        try:
            os.remove(playlist_file)
        except FileNotFoundError:
            pass
    else:
        with open(playlist_file, "w", encoding="utf-8") as file_write:
            file_write.writelines(lines)


def edit_file_folder(col, songs, replace):
    old_playlists = songs[0].playlists.split(";")
    path = songs[0].path()
    if col == "playlists":
        new_playlists = replace.split(";") if replace != "unsorted" else []
        old_path = songs[0].path()
        new_path = songs[0].path(dir=new_playlists[0])

        for playlist in old_playlists:
            if playlist not in new_playlists:
                __update_playlist(f"playlists/{playlist}.m3u", old_path=old_path)

        # if first changed, we need to update all
        if not old_playlists or (
            new_playlists and not new_playlists[0] == old_playlists[0]
        ):
            for playlist in new_playlists:
                if playlist in old_playlists:
                    __update_playlist(
                        f"playlists/{playlist}.m3u",
                        old_path=old_path,
                        new_path=new_path,
                    )
                else:
                    __update_playlist(f"playlists/{playlist}.m3u", new_path=new_path)
        else:
            for playlist in new_playlists:
                if playlist not in old_playlists and playlist != "":
                    __update_playlist(f"playlists/{playlist}.m3u", new_path=new_path)
    elif col == "title":
        for item in songs:
            from_file_path = item.path()
            replace_path = item.path(title=replace.replace("/", "|"))

            # update playlist data
            for playlist in old_playlists:
                __update_playlist(
                    f"playlists/{playlist}.m3u",
                    old_path=from_file_path,
                    new_path=replace_path,
                )

            if item.title != "" and replace != "" and os.path.exists(from_file_path):
                try:
                    os.rename(from_file_path, replace_path)
                except:
                    pass
                with taglib.File(replace_path, save_on_exit=True) as file:
                    file.tags["TITLE"] = replace.split(";")
    elif col == "yt_link":
        if songs[0].title != "" and os.path.exists(path):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
    elif col == "artists":
        if songs[0].title != "" and os.path.exists(path):
            with taglib.File(path, save_on_exit=True) as file:
                file.tags["ARTIST"] = replace.split(";")
    elif col == "genre":
        if songs[0].title != "" and os.path.exists(path):
            with taglib.File(path, save_on_exit=True) as file:
                file.tags["GENRE"] = replace.split(";")
    elif col == "year":
        if replace.isdigit() and songs[0].title != "" and os.path.exists(path):
            with taglib.File(path, save_on_exit=True) as file:
                file.tags["DATE"] = [str(replace)]
    elif col == "dir" and len(songs) > 1:
        for item in songs:
            for playlist in item.playlists.split(";"):
                __update_playlist(
                    f"playlists/{playlist}.m3u",
                    old_path=item.path(),
                    new_path=item.path(dir=replace),
                )

        if os.path.exists(songs[0].dir):
            try:
                os.mkdir(replace)
            except FileExistsError:
                pass
            for f in os.listdir(songs[0].dir):
                try:
                    os.rename(f"{songs[0].dir}/{f}", f"{replace}/{f}")
                    with taglib.File(path, save_on_exit=True) as file:
                        file.tags["ALBUM"] = replace.split(";")
                except:
                    print_error("Couln't move all files to the new folder folder")
                    pass
            # delete folder if empty
            try:
                os.removedirs(songs[0].dir)
            except OSError:
                pass
    elif col == "dir":
        for playlist in old_playlists:
            __update_playlist(
                f"playlists/{playlist}.m3u",
                old_path=songs[0].path(),
                new_path=songs[0].path(dir=replace),
            )
        if songs[0].title != "" and os.path.exists(songs[0].path()):
            with taglib.File(path, save_on_exit=True) as file:
                file.tags["ALBUM"] = replace.split(";")
            try:
                os.mkdir(replace)
            except FileExistsError:
                pass
            try:
                os.rename(
                    item.path(),
                    item.path(dir=replace),
                )
            except:
                pass
    elif col == "filetype":
        for playlist in old_playlists:
            __update_playlist(
                f"playlists/{playlist}.m3u",
                old_path=songs[0].path(),
                new_path=songs[0].path(filetype=replace),
            )


def __update_file_path(from_folder, to_folder, file_name, filetype):
    if from_folder != to_folder:
        try:
            os.mkdir(to_folder)
        except FileExistsError:
            pass
        try:
            os.rename(
                f"{from_folder}/{file_name}.{filetype}",
                f"{to_folder}/{file_name}.{filetype}",
            )
        except FileNotFoundError:
            pass
        try:
            os.removedirs(from_folder)
        except OSError:
            pass


def cellChanged(x, y):
    # fix for weird error when using tableButtonsChanged()
    if renewing_table or qTable.horizontalHeaderItem(y) is None:
        return

    changed_column = qTable.horizontalHeaderItem(y).text()
    replace_text = qTable.item(x, y).text().replace("'", "’")

    qTable.item(x, y).setText(replace_text)
    # check if there are other cells in the same column that had the same text (only if cell wasn't empty)

    try:
        queue = db_execute(
            f"SELECT rowid, {music_struct.sql_columns} FROM '{__get_selected_table()}' WHERE {changed_column}=(SELECT {changed_column} FROM '{__get_selected_table()}' WHERE rowid={qTable.item(x, 0).text()})"
        ).fetchall()
    except:
        print_error("problem queuing changes")
        return
    others = []
    for q in queue:
        others.append(song(select_data=q))
    if (
        len(others) > 1
        and others[0] is not None
        and others[0].title
        and changed_column not in ["playlists", "filetype"]
    ):
        msg_box = QMessageBox()
        msg_box.setText(
            f"There are {len(others) - 1} other items in '{changed_column}'.\nDo you want to change all of them too?"
        )
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        res = msg_box.exec()
        if res == QMessageBox.StandardButton.Yes:
            db_execute(
                f"UPDATE {__get_selected_table()} SET {changed_column}='{replace_text}' WHERE {changed_column}='{str(others[0].at(changed_column))}'"
            )
            db_commit()
            tableButtonsChanged()
            edit_file_folder(changed_column, others, replace_text)
            return
        elif res == QMessageBox.StandardButton.Cancel:
            qTable.cellChanged.disconnect()
            qTable.item(x, y).setText(str(others[0].at(changed_column)))
            qTable.cellChanged.connect(cellChanged)
            return

    __update_search()
    db_execute(
        f"UPDATE {__get_selected_table()} SET {changed_column}='{replace_text}' WHERE rowid={qTable.item(x, 0).text()}"
    )
    # only update dir if the current one was the same as the last first playlist
    if qTable.item(x, 9).text() == others[0].playlists.split(";")[0]:
        db_execute(
            f"UPDATE {__get_selected_table()} SET dir='{qTable.item(x, 1).text().split(';')[0]}' WHERE rowid={qTable.item(x, 0).text()}"
        )
        from_path = qTable.item(x, 9).text()
        to_path = qTable.item(x, 1).text().split(";")[0]

        __update_file_path(
            from_path if from_path else "unsorted",
            to_path if to_path else "unsorted",
            file_name=qTable.item(x, 2).text(),
            filetype=qTable.item(x, 10).text(),
        )

    db_commit()
    item = []
    for o in others:
        if int(qTable.item(x, 0).text()) == int(o.rowid):
            edit_file_folder(changed_column, [o], replace_text)
            break
    tableButtonsChanged()


def btn_push_del():
    row = qTable.currentIndex().row()
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setText("Do you really want to delete the row?")
    msg_box.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
    res = msg_box.exec()
    if res == QMessageBox.StandardButton.Yes:
        # TODO move to music_struct?
        dir = qTable.item(row, 8).text()
        title = qTable.item(row, 2).text()
        filetype = qTable.item(row, 10).text()
        if title == "":
            return
        db_execute(
            f"DELETE FROM '{__get_selected_table()}' WHERE rowid={qTable.item(row, 0).text()}"
        )
        db_commit()
        qTable.removeRow(row)
        from_path = (
            f"{dir}/{title.replace('/', '|')}.{filetype}"
            if dir and dir != "./"
            else f"unsorted/{title.replace('/', '|')}.{filetype}"
        )
        if os.path.exists(from_path):
            try:
                os.remove(from_path)
            except FileNotFoundError:
                pass


def btn_push_add_playlist():
    qTable.cellChanged.disconnect()
    selected = qTable.selectedIndexes()
    new_playlist = txt_playlist.toPlainText()
    for s in selected:
        row = s.row()
        # This is a mess. Im sorry
        if new_playlist in qTable.item(row, 1).text().split(";"):
            continue
        if qTable.item(row, 1).text() == "":
            db_execute(
                f"UPDATE {__get_selected_table()} SET (playlists, dir)=('{new_playlist}', '{new_playlist.split(';')[0]}') WHERE rowid={qTable.item(row, 0).text()}"
            )
            to_path = new_playlist
            __update_file_path(
                "unsorted",
                to_path,
                qTable.item(row, 2).text(),
                qTable.item(row, 10).text(),
            )
        else:
            new_playlists = qTable.item(row, 1).text() + ";" + new_playlist
            db_execute(
                f"UPDATE {__get_selected_table()} SET playlists='{new_playlists}' WHERE rowid={qTable.item(row, 0).text()}"
            )

        path = (
            f"{qTable.item(row, 9).text()}/{qTable.item(row, 2).text().replace('/', '|')}.{qTable.item(row, 10).text()}"
            if qTable.item(row, 9).text() != ""
            else f"{new_playlist.split(';')[0]}/{qTable.item(row, 2).text().replace('/', '|')}.{qTable.item(row, 10).text()}"
        )
        for p in new_playlist.split(";"):
            __update_playlist(f"playlists/{p}.m3u", new_path=path)
    qTable.cellChanged.connect(cellChanged)
    db_commit()
    tableButtonsChanged()


def btn_push_rem_playlist():
    qTable.cellChanged.disconnect()
    selected = qTable.selectedIndexes()
    rem_playlists = txt_playlist.toPlainText().split(";")
    for s in selected:
        row = s.row()
        # This is a mess. Im sorry
        cur_playlists = qTable.item(row, 1).text().split(";")
        cur_playlist_len = len(cur_playlists)
        cur_path = qTable.item(row, 9).text()
        file_name = f"{qTable.item(row, 2).text().replace('/', '|')}.{qTable.item(row, 10).text()}"

        if cur_playlist_len == 0:
            continue

        for p in rem_playlists:
            try:
                cur_playlists.remove(p)
            except ValueError:
                pass
        new_path = cur_playlists[0] if len(cur_playlists) else ""

        if cur_playlist_len == len(cur_playlists):
            continue
        elif cur_path == new_path:
            pass
        else:
            if new_path == "":
                for p in cur_playlists:
                    __update_playlist(
                        f"playlists/{p}.m3u",
                        old_path=f"{cur_path}/{file_name}",
                        new_path=f"unsorted/{file_name}",
                    )
            else:
                for p in cur_playlists:
                    __update_playlist(
                        f"playlists/{p}.m3u",
                        old_path=f"{cur_path}/{file_name}",
                        new_path=f"{new_path}/{file_name}",
                    )

        new_playlists = ";".join(cur_playlists)
        db_execute(
            f"UPDATE {__get_selected_table()} SET (playlists, dir)=('{new_playlists}','{new_path}') WHERE rowid={qTable.item(row, 0).text()}"
        )

        if new_path == "":
            for p in rem_playlists:
                __update_playlist(
                    f"playlists/{p}.m3u",
                    old_path=f"{cur_path}/{file_name}",
                )
        else:
            for p in rem_playlists:
                __update_playlist(
                    f"playlists/{p}.m3u",
                    old_path=f"{cur_path}/{file_name}",
                )
    qTable.cellChanged.connect(cellChanged)
    db_commit()
    tableButtonsChanged()


def btn_push_ren_yt():
    if qTable.currentRow() < 0:
        return
    id = qTable.item(qTable.currentRow(), 0).text()
    playlist = qTable.item(qTable.currentRow(), 1).text()
    title = qTable.item(qTable.currentRow(), 2).text()
    filetype = qTable.item(qTable.currentRow(), 10).text()
    artist = qTable.item(qTable.currentRow(), 3).text()
    res = music_parser.__get_new_yt_links(title, artist)

    question = ""
    if config.use_invidious:
        for i in range(5):
            question += f"({i + 1}) '{res[i]['title']} by '{res[i]['author']} : {res[i]['videoId']}\n"
    else:
        j = 1
        for i in range(5):
            try:
                question += f"({j}) '{res[i]['title']} by '{res[i]['artists'][0]['name']} : {res[i]['videoId']}\n"
                j += 1
            except:
                pass

    i = QInputDialog.getText(qTable, "renew YouTube link", question)[0]

    if i != "":
        try:
            _ = res[int(i)]
        except:
            return

        qTable.cellChanged.disconnect()
        path = f"{playlist}/{title.replace('/', '|')}.{filetype}"
        if title != "" and os.path.exists(path):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
        qTable.item(qTable.currentRow(), 7).setText(res[int(i) - 1]["videoId"])
        db_execute(
            f"UPDATE playlists SET yt_link='{res[int(i) - 1]['videoId']}' WHERE rowid={id}"
        )
        db_commit()
        qTable.cellChanged.connect(cellChanged)


def btn_push_sql():
    lbl_sql_ret.setVisible(True)
    try:
        dbRes = db_execute(str(txt_sql_field.toPlainText()))
        result = dbRes.fetchall()
        db_commit()
    except Exception as e:
        lbl_sql_ret.setText(str(e))
        return
    lbl_sql_ret.setText(str(result))

    if len(result) == 0:
        lbl_sql_ret.setVisible(False)
    tablesChanged()
    tableButtonsChanged()


def btn_push_links(abc, links=[]):
    if len(links) == 0:
        links = str(txt_sql_field.toPlainText()).split("\n")

    lbl_sql_ret.setVisible(True)
    lbl_sql_ret.setText("Loading...")

    lbl_sql_ret.setText(str(music_parser.parse_urls(database_path, links)))
    tableButtonsChanged()


def db_execute(text):
    # CHANGE_HERE: This is using SQLite commands but can be changed easily
    return db.execute(text)


def db_commit():
    # CHANGE_HERE: This is using SQLite commands but can be changed easily
    con.commit()


def main(database_link, urls=[]):
    global con
    global db
    global txt_search
    global qTable
    global txt_playlist
    global txt_sql_field
    global lbl_sql_ret
    global database_path
    global box_tables

    database_path = database_link

    app = QApplication([])
    window = QWidget()
    layout = QVBoxLayout(window)
    try:
        # CHANGE_HERE:
        con = sqlite3.connect(database_link)
        db = con.cursor()
    except:
        print_error("Couldn't connect to database!")
        exit()

    box_tables = QComboBox()
    layout.addWidget(box_tables)
    tablesChanged()

    txt_search = QPlainTextEdit("")
    txt_search.setPlaceholderText("search via RegEx: ")
    txt_search.setMaximumHeight(25)
    txt_search.textChanged.connect(__update_search)
    layout.addWidget(txt_search)

    qTable = TableView()
    layout.addWidget(qTable)

    box_add_playlist = QGroupBox()
    layout_add_playlist = QHBoxLayout()
    btn_add_playlist = QPushButton("Add selected to ")
    btn_add_playlist.clicked.connect(btn_push_add_playlist)
    txt_playlist = QPlainTextEdit("")
    txt_playlist.setPlaceholderText("playlist")
    txt_playlist.setMaximumHeight(25)
    btn_rem_playlist = QPushButton("remove from selected")
    btn_rem_playlist.clicked.connect(btn_push_rem_playlist)
    layout_add_playlist.addWidget(btn_add_playlist)
    layout_add_playlist.addWidget(txt_playlist)
    layout_add_playlist.addWidget(btn_rem_playlist)
    box_add_playlist.setLayout(layout_add_playlist)
    box_add_playlist.setMaximumHeight(55)
    layout.addWidget(box_add_playlist)

    btn_ren_yt = QPushButton("Renew selected yt_url")
    btn_ren_yt.clicked.connect(btn_push_ren_yt)
    layout.addWidget(btn_ren_yt)

    box_sql_links = QGroupBox()
    layout_sql_links = QGridLayout()

    txt_sql_field = QTextEdit("")
    txt_sql_field.setPlaceholderText("input your SQL or links here: ")
    layout_sql_links.addWidget(txt_sql_field, 0, 0)

    lbl_sql_ret = QLabel()
    lbl_sql_ret.setVisible(False)
    lbl_sql_ret.setWordWrap(True)
    lbl_sql_ret.setTextFormat(Qt.TextFormat.MarkdownText)
    layout_sql_links.addWidget(lbl_sql_ret, 0, 1)

    btnLinks = QPushButton("Search links")
    btnLinks.clicked.connect(btn_push_links)
    layout_sql_links.addWidget(btnLinks, 1, 0)

    btn_sql = QPushButton("Execute SQL")
    btn_sql.clicked.connect(btn_push_sql)
    layout_sql_links.addWidget(btn_sql, 1, 1)

    box_sql_links.setMaximumHeight(150)
    box_sql_links.setLayout(layout_sql_links)
    layout.addWidget(box_sql_links)

    tableButtonsChanged()

    window.show()

    # TODO get UI in separate Thread so that UI and parsing can happen at the same time
    if len(urls) > 0:
        txt_sql_field.setText("\n".join(urls))
        btn_push_links("", urls)

    sys.exit(app.exec())
