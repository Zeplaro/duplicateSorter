# coding: utf-8

import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from dataclasses import dataclass
from functools import partial
from pathlib import Path


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
        self.root_path = Path('C:/Users/robin/Photos/a trier')
        self.files = FileData(get_files(self.root_path))

        # UI stuff
        uic.loadUi('duplicateSorter.ui', self)

        QtWidgets.QApplication.setStyle("Fusion")
        self.setPalette(dark_palette)

        self.back_button = self.findChild(QtWidgets.QToolButton, 'back_button')
        self.path_line = self.findChild(QtWidgets.QLineEdit, 'path_line')
        self.path_line.setText(str(self.root_path))
        self.subfolders_check = self.findChild(QtWidgets.QCheckBox, 'subfolders_check')
        self.browse_button = self.findChild(QtWidgets.QPushButton, 'browse_button')

        self.folder_tree = self.findChild(QtWidgets.QTreeView, 'folder_tree')
        self.folder_tree.setModel(QtWidgets.QFileSystemModel())
        self.folder_tree.model().setFilter(QtCore.QDir.Dirs | QtCore.QDir.NoDotAndDotDot)
        self.folder_tree.setAlternatingRowColors(True)
        self.folder_tree.setSortingEnabled(True)
        self.folder_tree.setColumnHidden(1, True)
        self.folder_tree.setColumnHidden(2, True)
        self.folder_tree.setColumnHidden(3, True)
        self.folder_tree.setColumnWidth(0, 200)
        self.folder_tree.sortByColumn(0, QtCore.Qt.AscendingOrder)

        self.file_table = self.findChild(QtWidgets.QTableView, 'file_table')
        model = FileModel(self)
        self.file_table.setModel(model)
        self.file_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setSortingEnabled(True)

        # Extensions
        self.extension_list = self.findChild(QtWidgets.QListView, 'extension_list')
        self.extension_list.setModel(ExtensionModel(self, 'extension'))
        self.allextension_button = self.findChild(QtWidgets.QPushButton, 'allextension_button')
        self.noneextension_button = self.findChild(QtWidgets.QPushButton, 'noneextension_button')
        # Ignored
        self.ignored_list = self.findChild(QtWidgets.QListView, 'ignored_list')
        self.ignored_list.setModel(ExtensionModel(self, 'ignored'))
        self.allignored_button = self.findChild(QtWidgets.QPushButton, 'allignored_button')
        self.noneignored_button = self.findChild(QtWidgets.QPushButton, 'noneignored_button')

        # infos
        self.totalfiles_label = self.findChild(QtWidgets.QLabel, 'totalfiles_label')
        self.selectedfiles_label = self.findChild(QtWidgets.QLabel, 'selectedfiles_label')

        self.refresh_check = self.findChild(QtWidgets.QCheckBox, 'refresh_check')
        self.refresh_button = self.findChild(QtWidgets.QPushButton, 'refresh_button')

        self.ui_connections()

        self.set_root_dir()

    def ui_connections(self):
        self.back_button.clicked.connect(self.back_dir)
        self.path_line.editingFinished.connect(self.set_root_dir)
        self.subfolders_check.stateChanged.connect(self._set_files)
        self.browse_button.clicked.connect(self.browse)
        self.folder_tree.clicked.connect(self._set_files)
        self.allextension_button.clicked.connect(partial(self.all_none_buttons, 'extension', 'all'))
        self.noneextension_button.clicked.connect(partial(self.all_none_buttons, 'extension', 'none'))
        self.allignored_button.clicked.connect(partial(self.all_none_buttons, 'ignored', 'all'))
        self.noneignored_button.clicked.connect(partial(self.all_none_buttons, 'ignored', 'none'))

        self.refresh_button.clicked.connect(self.refresh)

    def back_dir(self):
        self.set_root_dir(self.root_path.parent)

    def browse(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(directory=self.path_line.text())
        self.path_line.setText(path)
        self.set_root_dir()

    def _set_files(self):
        if self.refresh_check.isChecked():
            self.set_files()

    def set_root_dir(self, path=None):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        if path:
            self.root_path = path
            self.path_line.setText(str(path))
        else:
            self.root_path = Path(self.path_line.text())
        if self.root_path.is_dir():
            self.folder_tree.model().setRootPath(str(self.root_path))
            self.folder_tree.setRootIndex(self.folder_tree.model().index(str(self.root_path)))
            self._set_files()
        QtWidgets.QApplication.restoreOverrideCursor()

    def set_files(self, index=None):
        print('Setting files')
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        file_path = Path(self.folder_tree.model().filePath(self.folder_tree.currentIndex()) or self.root_path)
        self.files = FileData(get_files(file_path, self.subfolders_check.isChecked()))
        self.totalfiles_label.setText(f"Total Files : {len(self.files)}")
        self.refresh_lists()
        QtWidgets.QApplication.restoreOverrideCursor()

    def all_none_buttons(self, type, button):
        if type == 'extension':
            if button == 'all':
                self.files.extension_state = [2] * len(self.files)
                self.files.ignored_state = [0] * len(self.files)
            else:
                self.files.extension_state = [0] * len(self.files)
        else:
            if button == 'all':
                self.files.ignored_state = [2] * len(self.files)
                self.files.extension_state = [0] * len(self.files)
            else:
                self.files.ignored_state = [0] * len(self.files)
        self.extension_list.model().layoutChanged.emit()
        self.ignored_list.model().layoutChanged.emit()

    def refresh_lists(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.file_table.model().layoutChanged.emit()
        self.extension_list.model().layoutChanged.emit()
        self.ignored_list.model().layoutChanged.emit()
        QtWidgets.QApplication.restoreOverrideCursor()

    def refresh(self, *args, **kwargs):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        print('refresh', args, kwargs)
        try:
            print('FILES', self.files.files)
            print("extensiosn", self.files.extensions)
            print("stems", self.files.stems)
            print("stems_count", self.files.stems_count)
        except Exception as e:
            print(e)
        self.set_root_dir()
        if not self.refresh_check.isChecked():
            self.set_files()
        QtWidgets.QApplication.restoreOverrideCursor()


class FileModel(QtCore.QAbstractTableModel):
    def __init__(self, ui):
        super(FileModel, self).__init__()
        self.ui = ui

    def rowCount(self, index):
        return len(self.ui.files)

    def columnCount(self, index):
        return 3

    def data(self, index, role=QtCore.Qt.DisplayRole):
        row = index.row()
        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return self.ui.files[row].name
            elif column == 1:
                return self.ui.files[row].suffix
            elif column == 2:
                return self.ui.files[row].size

    def headerData(self, column, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if column == 0:
                    return "Name"
                elif column == 1:
                    return "Type"
                elif column == 2:
                    return "Size"

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled


def get_files(path, withsubfolders=False):
    files = []
    subfolders = []
    for item in path.iterdir():
        if item.is_file():
            name = item.name
            size = str(round(item.stat().st_size/(1024**2), 2)) + ' MB'
            suffix = item.suffix
            stem = item.stem
            files.append(File(name, suffix, size, stem))
        elif withsubfolders:
            subfolders.append(item)
    for item in subfolders:
        files.extend(get_files(item, withsubfolders))
    return files


class FileData:
    def __init__(self, files: list):
        self.files = files
        self.extensions = list(set(file.suffix for file in files))
        self.stems = [file.stem for file in files]
        self.stems_count = {stem: self.stems.count(stem) for stem in self.stems}
        self.extension_state = [0] * len(files)
        self.ignored_state = [0] * len(files)

    def __len__(self):
        return len(self.files)

    def __getitem__(self, item):
        return self.files[item]


@dataclass
class File:
    name: str
    suffix: str
    size: str
    stem: str

    def __repr__(self):
        return self.name


class ExtensionModel(QtCore.QAbstractListModel):
    def __init__(self, ui, type):
        super(ExtensionModel, self).__init__()
        self.ui = ui
        self.type = type

    def rowCount(self, index):
        return len(self.ui.files.extensions)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            return self.ui.files.extensions[index.row()] or 'None'
        elif role == QtCore.Qt.CheckStateRole:
            if self.type == 'extension':
                return self.ui.files.extension_state[index.row()]
            else:
                return self.ui.files.ignored_state[index.row()]

    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.CheckStateRole:
            if self.type == 'extension':
                if value == 2:
                    self.ui.files.ignored_state[index.row()] = 0
                    self.ui.ignored_list.model().dataChanged.emit(index, index)
                self.ui.files.extension_state[index.row()] = value
            else:
                if value == 2:
                    self.ui.files.extension_state[index.row()] = 0
                    self.ui.extension_list.model().dataChanged.emit(index, index)
                self.ui.files.ignored_state[index.row()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable


if __name__ == '__main__':
    launch_ui()
