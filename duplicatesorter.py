# coding: utf-8
from PyQt5 import QtWidgets, QtCore, QtGui, uic
import sys
from os import path as ospath
from pathlib import Path
from shutil import copyfile
import subprocess
from functools import partial
from time import time
import platform


qt_refresh = QtWidgets.QApplication.processEvents

dark_palette = QtGui.QPalette()
dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(43, 43, 43))
dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(60, 63, 65))
dark_palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(190, 190, 190))
dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(50, 53, 55))
dark_palette.setColor(QtGui.QPalette.Text, QtGui.QColor(230, 230, 230))
dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(60, 63, 65))
dark_palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(200, 200, 200))
dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(80, 113, 135))
dark_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Highlight, QtGui.QColor(80, 80, 80))
dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.white)

default_palette = QtGui.QPalette()
default_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(245, 245, 245))


def launch_ui():
    app = QtWidgets.QApplication(sys.argv)
    ui = MainUI()
    ui.show()
    sys.exit(app.exec_())


class MainUI(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainUI, self).__init__()
        uic.loadUi('duplicateSorter.ui', self)

        QtWidgets.QApplication.setStyle("Fusion")
        self.setPalette(dark_palette)


if __name__ == '__main__':
    launch_ui()
