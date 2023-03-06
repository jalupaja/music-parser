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
import eyed3
import os
import sys
import sqlite3

import music_parser
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


def edit_file_folder(col, arr, replace):
    from_path = arr[0][0] if arr[0][0] and arr[0][0] != "./" else "./unsorted"
    if replace == "":
        replace = "unsorted"

    if col == "playlists":
        new_playlists = replace.split(";") if replace != "unsorted" else []
        old_playlists = arr[0][0].split(";")
        old_path = (
            f"{arr[0][1]}/{arr[0][2].replace('/', '|')}.mp3"
            if arr[0][1] != ""
            else f"{replace.split(';')[0]}/{arr[0][2].replace('/', '|')}.mp3"
        )
        # only change if dir was changed -> if dir == last first playlist
        if arr[0][1] == arr[0][0].split(";")[0]:
            new_path = (
                f"{replace.split(';')[0]}/{arr[0][2].replace('/', '|')}.mp3"
                if arr[0][1] != ""
                else f"{replace.split(';')[0]}/{arr[0][2].replace('/', '|')}.mp3"
            )
        else:
            new_path = (
                f"{arr[0][1]}/{arr[0][2].replace('/', '|')}.mp3"
                if arr[0][1] != ""
                else f"{replace.split(';')[0]}/{arr[0][2].replace('/', '|')}.mp3"
            )
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
        for item in arr:
            from_file_path = f"{item[1]}/{item[0].replace('/', '|')}.mp3"
            replace_path = f"{item[1]}/{replace.replace('/', '|')}.mp3"

            # update playlist data
            for playlist in item[4].split(";"):
                __update_playlist(
                    f"playlists/{playlist}.m3u",
                    old_path=from_file_path,
                    new_path=replace_path,
                )

            if item[2] != "" and replace != "" and os.path.exists(from_file_path):
                try:
                    os.rename(from_file_path, replace_path)
                except:
                    pass
                file = eyed3.load(replace_path)
                file.tag.title = replace
                file.tag.save()
    elif col == "yt_link":
        path = f"{arr[0][1]}/{arr[0][2].replace('/', '|')}.mp3"
        if arr[0][2] != "" and os.path.exists(path):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
    elif col == "artists":
        path = f"{arr[0][1]}/{arr[0][2].replace('/', '|')}.mp3"
        if arr[0][2] != "" and os.path.exists(path):
            file = eyed3.load(path)
            file.tag.artist = replace.replace(",", ";")
            file.tag.save()
    elif col == "genre":
        path = f"{arr[0][1]}/{arr[0][2].replace('/', '|')}.mp3"
        if arr[0][2] != "" and os.path.exists(path):
            file = eyed3.load(path)
            file.tag.genre = replace.replace(",", ";")
            file.tag.save()
    elif col == "year":
        path = f"{arr[0][1]}/{arr[0][2].replace('/', '|')}.mp3"
        if replace.isdigit() and arr[0][2] != "" and os.path.exists(path):
            file = eyed3.load(path)
            file.tag.original_release_date = replace
            file.tag.year = replace
            file.tag.release_date = replace
            file.tag.save()
    elif col == "dir" and len(arr) > 1:
        for a in arr:
            for playlist in a[4].split(";"):
                __update_playlist(
                    f"playlists/{playlist}.m3u",
                    old_path=f"{from_path}/{a[2]}.mp3",
                    new_path=f"{replace}/{a[2]}.mp3",
                )

        if os.path.exists(from_path):
            try:
                os.mkdir(replace)
            except FileExistsError:
                pass
            for f in os.listdir(from_path):
                try:
                    os.rename(f"{from_path}/{f}", f"{replace}/{f}")
                    if f.endswith("mp3"):
                        file = eyed3.load(f"{replace}/{f}")
                        file.tag.album = replace
                        file.tag.save()
                except:
                    print_error("Couln't move all files to the new folder folder")
                    pass
            # delete folder if empty
            try:
                os.removedirs(from_path)
            except OSError:
                pass
    elif col == "dir":
        for playlist in arr[0][4].split(";"):
            __update_playlist(
                f"playlists/{playlist}.m3u",
                old_path=f"{from_path}/{arr[0][2].replace('/', '|')}.mp3",
                new_path=f"{replace}/{arr[0][2].replace('/', '|')}.mp3",
            )
        if arr[0][2] != "" and os.path.exists(
            f"{from_path}/{arr[0][2].replace('/', '|')}.mp3"
        ):
            try:
                os.mkdir(replace)
            except FileExistsError:
                pass
            try:
                os.rename(
                    f"{from_path}/{arr[0][2].replace('/', '|')}.mp3",
                    f"{replace}/{arr[0][2].replace('/', '|')}.mp3",
                )
            except:
                pass
            file = eyed3.load(f"{replace}/{arr[0][2].replace('/', '|')}.mp3")
            file.tag.album = replace
            file.tag.save()
            try:
                os.rename(
                    f"{from_path}/{arr[0][2].replace('/', '|')}.mp3",
                    f"{replace}/{arr[0][2].replace('/', '|')}.mp3",
                )
            except:
                pass


def __update_file_path(from_folder, to_folder, file_name):
    if from_folder != to_folder:
        try:
            os.mkdir(to_folder)
        except FileExistsError:
            pass
        try:
            os.rename(f"{from_folder}/{file_name}", f"{to_folder}/{file_name}")
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

    qTable.item(x, y).setText(qTable.item(x, y).text().replace("'", "’"))
    # check if there are other cells in the same column that had the same text (only if cell wasn't empty)
    try:
        others = db_execute(
            f"SELECT {qTable.horizontalHeaderItem(y).text()},dir,title,rowid,playlists FROM '{__get_selected_table()}' WHERE {qTable.horizontalHeaderItem(y).text()}=(SELECT {qTable.horizontalHeaderItem(y).text()} FROM '{__get_selected_table()}' WHERE rowid={qTable.item(x, 0).text()})"
        ).fetchall()
    except:
        return

    if (
        len(others) > 1
        and others[0][0]
        and qTable.horizontalHeaderItem(y).text() != "playlists"
    ):
        msg_box = QMessageBox()
        msg_box.setText(
            f"There are {len(others) - 1} other items in '{qTable.horizontalHeaderItem(y).text()}'.\nDo you want to change all of them too?"
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
                f"UPDATE {__get_selected_table()} SET {qTable.horizontalHeaderItem(y).text()}='{qTable.item(x, y).text()}' WHERE {qTable.horizontalHeaderItem(y).text()}='{str(others[0][0])}'"
            )
            db_commit()
            tableButtonsChanged()
            edit_file_folder(
                qTable.horizontalHeaderItem(y).text(), others, qTable.item(x, y).text()
            )
            return
        elif res == QMessageBox.StandardButton.Cancel:
            qTable.cellChanged.disconnect()
            qTable.item(x, y).setText(str(others[0][0]))
            qTable.cellChanged.connect(cellChanged)
            return

    __update_search()
    db_execute(
        f"UPDATE {__get_selected_table()} SET {qTable.horizontalHeaderItem(y).text()}='{qTable.item(x, y).text()}' WHERE rowid={qTable.item(x, 0).text()}"
    )
    # only update dir if the current one was the same as the last first playlist
    if qTable.item(x, 9).text() == others[0][4].split(";")[0]:
        db_execute(
            f"UPDATE {__get_selected_table()} SET dir='{qTable.item(x, 1).text().split(';')[0]}' WHERE rowid={qTable.item(x, 0).text()}"
        )
        from_path = qTable.item(x, 9).text()
        to_path = qTable.item(x, 1).text().split(";")[0]
        __update_file_path(
            from_path if from_path else "unsorted",
            to_path if to_path else "unsorted",
            qTable.item(x, 2).text() + ".mp3",
        )

    db_commit()
    item = []
    for o in others:
        if int(qTable.item(x, 0).text()) == int(o[3]):
            edit_file_folder(
                qTable.horizontalHeaderItem(y).text(), [o], qTable.item(x, y).text()
            )
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
        dir = qTable.item(row, 8).text()
        title = qTable.item(row, 2).text()
        if title == "":
            return
        db_execute(
            f"DELETE FROM '{__get_selected_table()}' WHERE rowid={qTable.item(row, 0).text()}"
        )
        db_commit()
        qTable.removeRow(row)
        from_path = (
            f"{dir}/{title.replace('/', '|')}.mp3"
            if dir and dir != "./"
            else f"unsorted/{title.replace('/', '|')}.mp3"
        )
        if os.path.exists(from_path):
            try:
                os.remove(from_path)
            except FileNotFoundError:
                pass


def btn_push_playlist():
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
                f"UPDATE {__get_selected_table()} SET (playlists, dir)=('{new_playlist}', '{new_playlist}') WHERE rowid={qTable.item(row, 0).text()}"
            )
            to_path = new_playlist
            __update_file_path("unsorted", to_path, qTable.item(row, 2).text() + ".mp3")
        else:
            new_playlists = qTable.item(row, 1).text() + ";" + new_playlist
            db_execute(
                f"UPDATE {__get_selected_table()} SET playlists='{new_playlists}' WHERE rowid={qTable.item(row, 0).text()}"
            )

        path = (
            f"{qTable.item(row, 9).text()}/{qTable.item(row, 2).text().replace('/', '|')}.mp3"
            if qTable.item(row, 9).text() != ""
            else f"{new_playlist}/{qTable.item(row, 2).text().replace('/', '|')}.mp3"
        )
        __update_playlist(f"playlists/{new_playlist}.m3u", new_path=path)
    qTable.cellChanged.connect(cellChanged)
    db_commit()
    tableButtonsChanged()


def btn_push_ren_yt():
    if qTable.currentRow() < 0:
        return
    id = qTable.item(qTable.currentRow(), 0).text()
    playlist = qTable.item(qTable.currentRow(), 1).text()
    title = qTable.item(qTable.currentRow(), 2).text()
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
        path = f"{playlist}/{title.replace('/', '|')}.mp3"
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
    btn_add_playlist.clicked.connect(btn_push_playlist)
    txt_playlist = QPlainTextEdit("")
    txt_playlist.setPlaceholderText("playlist")
    txt_playlist.setMaximumHeight(25)
    layout_add_playlist.addWidget(btn_add_playlist)
    layout_add_playlist.addWidget(txt_playlist)
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
