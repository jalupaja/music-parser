#!/usr/bin/env python3

# This file is originally from https://github.com/jalupaja/SQLite-gui
# and has been edited to add some functionality to this project

# TODO change layout and overall looks (will probably never happen...)

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget, QTableWidgetItem, QVBoxLayout, QRadioButton, QTextEdit, QLabel, QPushButton, QMessageBox, QInputDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, Qt
import eyed3
import os
import sys
import sqlite3

import music_parser


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
        items = qTable.findItems(search, Qt.MatchRegularExpression)
        searched_rows = []
        for i in items:
            searched_rows.append(i.row())
        for row in range(qTable.rowCount()):
            qTable.setRowHidden(row, row not in searched_rows)


def __update_search():
    search(txt_search.toPlainText())


def __get_selected_table():
    for btn in tableButtons:
        if btn.isChecked():
            return btn.text()
    return None


def tableButtonsChanged():
    global qTable

    selected_table = __get_selected_table()
    if selected_table == None:
        tableButtons[0].toggle()
        return

    global renewing_table
    renewing_table = True

    qTable.clear()
    data = db_execute(f"SELECT rowid,* FROM {selected_table}")
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
                    nItem.setData(Qt.DisplayRole, rows[rowCount][colCount + rowid_changed])
                    qTable.setItem(rowCount, colCount, nItem)
                    if colCount == 0:
                        nItem.setFlags(nItem.flags() & Qt.ItemIsEditable)
            rowCount += 1
    renewing_table = False
    qTable.sortByColumn(0, Qt.AscendingOrder)
    __update_search()


def edit_file_folder(col, arr, replace):
    from_path = arr[0][0] if arr[0][0] and arr[0][0] != "./" else "unsorted"
    if replace == "":
        replace = "unsorted"

    if col == "playlist_name" and len(arr) > 1:
        if os.path.exists(from_path):
            for f in os.listdir(replace):
                if f.endswith("mp3"):
                    file = eyed3.load(f"{replace}/{f}")
                    file.tag.album = replace
                    file.tag.save()
                try:
                    os.rename(f"{from_path}/{arr[0][2].replace('/', '|')}.mp3", f"{replace}/{arr[0][2].replace('/', '|')}.mp3")
                except:
                    pass
    elif col == "playlist_name":
        if arr[0][2] != "" and os.path.exists(f"{from_path}/{arr[0][2].replace('/', '|')}.mp3"):
            try:
                os.mkdir(replace)
            except:
                pass
            try:
                os.rename(f"{from_path}/{arr[0][2].replace('/', '|')}.mp3", f"{replace}/{arr[0][2].replace('/', '|')}.mp3")
            except:
                pass
            file = eyed3.load(f"{replace}/{arr[0][2].replace('/', '|')}.mp3")
            file.tag.album = replace
            file.tag.save()
    elif col == "title":
        for item in arr:
            from_file_path = f"{item[1]}/{item[0].replace('/', '|')}.mp3"
            replace_path = f"{item[1]}/{replace.replace('/', '|')}.mp3"
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
            except:
                pass
    elif col == "artists":
        path = f"{arr[0][1]}/{arr[0][2].replace('/', '|')}.mp3"
        if arr[0][2] != "" and os.path.exists(path):
            file = eyed3.load(path)
            file.tag.artist = replace
            file.tag.save()
    elif col == "year":
        path = f"{arr[0][1]}/{arr[0][2].replace('/', '|')}.mp3"
        if arr[0][2] != "" and os.path.exists(path):
            file = eyed3.load(path)
            file.tag.original_release_date = replace
            file.tag.save()


def cellChanged(x, y):
    # fix for weird error when using tableButtonsChanged()
    if renewing_table or qTable.horizontalHeaderItem(y) is None:
        return

    # check if there are other cells in the same column that had the same text (only if cell wasn't empty)
    try:
        others = db_execute(f"SELECT {qTable.horizontalHeaderItem(y).text()},playlist_name,title,rowid FROM {__get_selected_table()} WHERE {qTable.horizontalHeaderItem(y).text()}=(SELECT {qTable.horizontalHeaderItem(y).text()} FROM {__get_selected_table()} WHERE rowid={qTable.item(x, 0).text()})").fetchall()
    except:
        return

    if len(others) > 1 and others[0][0]:
        msg_box = QMessageBox()
        msg_box.setText(f"There are {len(others) - 1} other items in '{qTable.horizontalHeaderItem(y).text()}'.\nDo you want to change all of them too?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.No)
        res = msg_box.exec()
        if res == QMessageBox.Yes:
            db_execute(f"UPDATE {__get_selected_table()} SET {qTable.horizontalHeaderItem(y).text()}='{qTable.item(x, y).text()}' WHERE {qTable.horizontalHeaderItem(y).text()}='{str(others[0][0])}'")
            db_commit()
            tableButtonsChanged()
            edit_file_folder(qTable.horizontalHeaderItem(y).text(), others, qTable.item(x, y).text())
            return
        elif res == QMessageBox.Cancel:
            qTable.cellChanged.disconnect()
            qTable.item(x, y).setText(str(others[0][0]))
            qTable.cellChanged.connect(cellChanged)
            return

    __update_search()
    db_execute(f"UPDATE {__get_selected_table()} SET {qTable.horizontalHeaderItem(y).text()}='{qTable.item(x, y).text()}' WHERE rowid={qTable.item(x, 0).text()}")
    db_commit()
    item = []
    for o in others:
        if int(qTable.item(x, 0).text()) == int(o[3]):
            edit_file_folder(qTable.horizontalHeaderItem(y).text(), [o], qTable.item(x, y).text())
            break


def btn_push_del():
    row = qTable.currentIndex().row()
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setText("Do you really want to delete the row?")
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg_box.setDefaultButton(QMessageBox.Yes)
    res = msg_box.exec()
    if res == QMessageBox.Yes:
        playlist = qTable.item(row, 1).text()
        title = qTable.item(row, 2).text()
        if title == "":
            return
        db_execute(f"DELETE FROM {__get_selected_table()} WHERE rowid={qTable.item(row, 0).text()}")
        db_commit()
        qTable.removeRow(row)
        from_path = f"{playlist}/{title.replace('/', '|')}.mp3" if playlist and playlist != "./" else f"unsorted/{title.replace('/', '|')}.mp3"
        if os.path.exists(from_path):
            try:
                os.remove(from_path)
            except:
                pass


def btn_push_ren_yt():
    if qTable.currentRow() < 0:
        return
    id = qTable.item(qTable.currentRow(), 0).text()
    title = qTable.item(qTable.currentRow(), 2).text()
    artist = qTable.item(qTable.currentRow(), 3).text()
    res = music_parser.__get_new_yt_links(title, artist)

    question = ""
    for i in range(5):
        question += f"({i + 1}) '{res[i]['title']} by '{res[i]['author']} : {res[i]['videoId']}\n"

    i = QInputDialog.getText(qTable, "renew YouTube link", question)[0]

    if i != "":
        try:
            _ = res[int(i)]
        except:
            return

        qTable.cellChanged.disconnect()
        qTable.item(qTable.currentRow(), 6).setText(res[int(i) - 1]['videoId'])
        db_execute(f"UPDATE playlists SET yt_link='{res[int(i) - 1]['videoId']}' WHERE rowid={id}")
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
    global tableButtons
    global txt_search
    global qTable
    global txt_sql_field
    global lbl_sql_ret
    global database_path

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

    tables = db_execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    tableButtons = []
    for table in tables:
        btn = QRadioButton(table[0])
        btn.clicked.connect(tableButtonsChanged)
        tableButtons.append(btn)
        layout.addWidget(btn)

    txt_search = QTextEdit("")
    txt_search.setAcceptRichText(False)
    txt_search.setPlaceholderText("search via RegEx: ")
    txt_search.setMaximumHeight(25)
    txt_search.textChanged.connect(__update_search)
    layout.addWidget(txt_search)

    qTable = TableView()
    layout.addWidget(qTable)

    btn_ren_yt = QPushButton("Renew selected yt_url")
    btn_ren_yt.clicked.connect(btn_push_ren_yt)
    layout.addWidget(btn_ren_yt)

    txt_sql_field = QTextEdit("")
    txt_sql_field.setAcceptRichText(False)
    txt_sql_field.setPlaceholderText("input your SQL or links here: ")
    txt_sql_field.setMaximumHeight(50)
    layout.addWidget(txt_sql_field)

    lbl_sql_ret = QLabel()
    lbl_sql_ret.setVisible(False)
    lbl_sql_ret.setWordWrap(True)
    lbl_sql_ret.setTextFormat(Qt.MarkdownText)
    layout.addWidget(lbl_sql_ret)

    btn_sql = QPushButton("Execute SQL")
    btn_sql.clicked.connect(btn_push_sql)
    layout.addWidget(btn_sql)

    btnLinks = QPushButton("Search links")
    btnLinks.clicked.connect(btn_push_links)
    layout.addWidget(btnLinks)

    if len(tableButtons) > 0:
        tableButtons[0].toggle()
        tableButtonsChanged()

    window.show()

    # TODO get UI in separate Thread so that UI and parsing can happen at the same time
    if len(urls) > 0:
        txt_sql_field.setText("\n".join(urls))
        btn_push_links("", urls)

    sys.exit(app.exec_())
