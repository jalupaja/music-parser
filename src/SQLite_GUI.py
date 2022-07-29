#!/usr/bin/env python3

# This file is originally from https://github.com/jalupaja/SQLite-gui
# and has been edited to add some functionality to this project

# TODO change layout and overall looks (will probably never happen...)

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget,QTableWidgetItem,QVBoxLayout,QRadioButton,QTextEdit,QLabel,QPushButton,QMessageBox,QInputDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot,Qt
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

    qTable.clear()
    data = db_execute(f"SELECT rowid,* FROM {selected_table}")
    cols = data.description
    rows = data.fetchall()

    headers = []
    for header in cols:
        headers.append(header[0])

    qTable.setColumnCount(len(data.description))
    qTable.setRowCount(len(rows))
    rowLen = len(rows)
    colLen = len(rows[0])
    for rowCount in range(rowLen):
        for colCount in range(colLen):
            nItem = QTableWidgetItem(str(rows[rowCount][colCount]))
            qTable.setItem(rowCount, colCount, nItem)
            if colCount == 0:
                nItem.setFlags(nItem.flags() & Qt.ItemIsEditable)

        rowCount += 1
    qTable.setHorizontalHeaderLabels(headers)


def cellChanged(x, y):
    # fix for weird error when using tableButtonsChanged()
    if qTable.horizontalHeaderItem(y) == None:
        return

    # check if there are other cells in the same column that had the same text
    try:
        others = db_execute(f"SELECT {qTable.horizontalHeaderItem(y).text()} FROM {__get_selected_table()} WHERE {qTable.horizontalHeaderItem(y).text()}=(SELECT {qTable.horizontalHeaderItem(y).text()} FROM {__get_selected_table()} WHERE rowid={qTable.item(x, 0).text()})").fetchall()
    except:
        return

    if len(others) > 1:
        msgBox = QMessageBox()
        msgBox.setText(f"There are {len(others) - 1} other items in '{qTable.horizontalHeaderItem(y).text()}'.\nDo you want to change all of them too?")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.No)
        res = msgBox.exec()
        if res == QMessageBox.Yes:
            db_execute(f"UPDATE {__get_selected_table()} SET {qTable.horizontalHeaderItem(y).text()}='{qTable.item(x, y).text()}' WHERE {qTable.horizontalHeaderItem(y).text()}='{str(others[0][0])}'")
            db_commit()
            tableButtonsChanged()
            return
        elif res == QMessageBox.Cancel:
            qTable.cellChanged.disconnect()
            qTable.item(x, y).setText(str(others[0][0]))
            qTable.cellChanged.connect(cellChanged)
            return

    db_execute(f"UPDATE {__get_selected_table()} SET {qTable.horizontalHeaderItem(y).text()}='{qTable.item(x, y).text()}' WHERE rowid={qTable.item(x, 0).text()}")
    db_commit()


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
    print(links)
    if len(links) == 0:
        links = str(txt_sql_field.toPlainText()).split("\n")
    print(links)

    lbl_sql_ret.setVisible(True)
    lbl_sql_ret.setText("Loading...")

    lbl_sql_ret.setText(str(music_parser.parse_urls(databasePath, links, downloadPath)))
    tableButtonsChanged()


def db_execute(text):
    # CHANGE_HERE: This is using SQLite commands but can be changed easily
    return db.execute(text)


def db_commit():
    # CHANGE_HERE: This is using SQLite commands but can be changed easily
    con.commit()


def main(databaseLink, urls=[], download=""):
    global con
    global db
    global qTable
    global tableButtons
    global txt_sql_field
    global lbl_sql_ret

    global databasePath
    global downloadPath

    databasePath = databaseLink
    downloadPath = download

    app = QApplication([])
    window = QWidget()
    layout = QVBoxLayout(window)
    try:
        # CHANGE_HERE:
        con = sqlite3.connect(databaseLink)
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

    btnSQL = QPushButton("Execute SQL")
    btnSQL.clicked.connect(btn_push_sql)
    layout.addWidget(btnSQL)

    btnLinks = QPushButton("Search links")
    btnLinks.clicked.connect(btn_push_links)
    layout.addWidget(btnLinks)

    if len(tableButtons) > 0:
        tableButtons[0].toggle()
        tableButtonsChanged()

    if len(urls) > 0:
        txt_sql_field.setText("\n".join(urls))
        btn_push_links("", urls)

    window.show()
    sys.exit(app.exec_())


if __name__=="__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1], [], sys.argv)
    else:
        print_error("You have to give a link to the database")
