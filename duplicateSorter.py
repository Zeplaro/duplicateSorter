# coding: utf-8

import sys
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from shutil import copy2, move
from time import perf_counter
from subprocess import Popen

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
        self.root_path: Path = Path.home()
        self.files: [File, ] = []  # list of all files listed in the file_table view
        self.extensions: [str, ] = []  # list of all extensions listed in the extension_list and ignored_list views
        self.extension_states: [bool, ] = []  # list of state per extensions
        self.ignored_states: [bool, ] = []  # list of state per ignored
        self.selected_files: [File, ] = []  # list of selected/highlighted files from file_table view

        # .ui file loading, fullpath needed for pyinstaller
        uic.loadUi('D:/Robin/Work/Python/duplicateSorter/duplicateSorter.ui', self)

        QtWidgets.QApplication.setStyle("Fusion")
        self.setPalette(dark_palette)
        self.setWindowTitle('Duplicate Sorter')
        # icon fullpath needed for pyinstaller
        self.setWindowIcon(QtGui.QIcon('D:/Robin/Work/Python/duplicateSorter/duplicateSorter.ico'))

        self.back_button = self.findChild(QtWidgets.QToolButton, 'back_button')
        self.path_line = self.findChild(QtWidgets.QLineEdit, 'path_line')
        self.path_line.setText(str(self.root_path))
        self.subfolders_check = self.findChild(QtWidgets.QCheckBox, 'subfolders_check')
        self.browse_button = self.findChild(QtWidgets.QPushButton, 'browse_button')

        # folder tree
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

        # tables splitter
        tables_splitter = self.findChild(QtWidgets.QSplitter, 'tables_splitter')
        tables_splitter.setSizes([1, 1000])  # Setting the splitter to minimum size on left part

        # file table
        self.file_table = self.findChild(QtWidgets.QTableView, 'file_table')
        model = FileModel(self)
        self.file_table.setModel(model)
        self.file_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setSortingEnabled(True)
        self.file_table.sortByColumn(0, QtCore.Qt.AscendingOrder)

        # main splitter
        main_splitter = self.findChild(QtWidgets.QSplitter, 'main_splitter')
        main_splitter.setSizes([1000, 1])  # Setting the splitter to minimum size on bottom part

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

        # Actions
        self.actionbuttons_group = self.findChild(QtWidgets.QButtonGroup, 'actionbuttons_group')

        # Process
        self.refresh_check = self.findChild(QtWidgets.QCheckBox, 'refresh_check')
        self.refresh_button = self.findChild(QtWidgets.QPushButton, 'refresh_button')
        self.process_button = self.findChild(QtWidgets.QPushButton, 'process_button')
        self.subfolder_line = self.findChild(QtWidgets.QLineEdit, 'subfolder_line')
        self.progress_bar = self.findChild(QtWidgets.QProgressBar, 'progress_bar')
        self.progress_bar.setValue(0)

        self.ui_connections()

        self.set_root_dir()

    def ui_connections(self):
        self.back_button.clicked.connect(self.back_dir)
        self.path_line.editingFinished.connect(self.set_root_dir)
        self.subfolders_check.stateChanged.connect(self._set_files)
        self.browse_button.clicked.connect(self.browse)
        self.folder_tree.clicked.connect(self._set_files)
        self.folder_tree.doubleClicked.connect(self.folder_tree_double_clicked)
        self.folder_tree.activated.connect(self._set_files)
        self.file_table.doubleClicked.connect(self.open_file_in_explorer)
        self.allextension_button.clicked.connect(partial(self.all_none_buttons, 'extension', 'all'))
        self.noneextension_button.clicked.connect(partial(self.all_none_buttons, 'extension', 'none'))
        self.allignored_button.clicked.connect(partial(self.all_none_buttons, 'ignored', 'all'))
        self.noneignored_button.clicked.connect(partial(self.all_none_buttons, 'ignored', 'none'))

        self.refresh_button.clicked.connect(self.refresh)
        self.process_button.clicked.connect(self.process)

    def back_dir(self):
        self.set_root_dir(self.root_path.parent)

    def browse(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(directory=self.path_line.text())
        self.path_line.setText(path)
        self.set_root_dir()

    def _set_files(self):
        if self.refresh_check.isChecked():
            self.set_files()

    def set_root_dir(self, path: Path = None):
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

    def set_files(self):
        self.statusBar().showMessage("Updating file list...")
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        start_time = perf_counter()
        file_path = Path(self.folder_tree.model().filePath(self.folder_tree.currentIndex()) or self.root_path)

        # saves checked extensions and checked ignored to re set them latter
        checked_extensions = [x for x, y in zip(self.extensions, self.extension_states) if y]
        checked_ignored = [x for x, y in zip(self.extensions, self.ignored_states) if y]
        self.files = get_files(file_path, self.subfolders_check.isChecked())
        self.sort_files()
        self.extensions = list(set(file.suffix for file in self.files))
        # re sets the saved checked extensions and checked ignored
        self.extension_states = [2 if x in checked_extensions else 0 for x in self.extensions]
        self.ignored_states = [2 if x in checked_ignored else 0 for x in self.extensions]
        self.selected_files = self.get_selected_files()

        self.totalfiles_label.setText(f"Total Files : {len(self.files)}")
        self.refresh_lists()
        self.statusBar().showMessage(f"File list updated in : {perf_counter()-start_time:.3f}sec")
        QtWidgets.QApplication.restoreOverrideCursor()

    def sort_files(self, column=None, order=None):
        if column is None:
            column = self.file_table.horizontalHeader().sortIndicatorSection()
        if order is None:
            order = self.file_table.horizontalHeader().sortIndicatorOrder()
        if column == 0:
            self.files.sort(key=lambda x: x.name, reverse=bool(order))
        elif column == 1:
            self.files.sort(key=lambda x: x.suffix, reverse=bool(order))
        elif column == 2:
            self.files.sort(key=lambda x: x.size, reverse=bool(order))

    def get_selected_files(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        start_time = perf_counter()

        selected = []
        checked_extensions = [x for x, y in zip(self.extensions, self.extension_states) if y]
        checked_ignored = [x for x, y in zip(self.extensions, self.ignored_states) if y]
        stems = [file.stem for file in self.files if file.suffix not in checked_ignored]
        stems_count = {file.stem: stems.count(file.stem) for file in self.files}
        for file in self.files:
            if file.suffix in checked_extensions:
                if stems_count[file.stem] > 1:
                    selected.append(file)

        QtWidgets.QApplication.restoreOverrideCursor()
        self.statusBar().showMessage(f"Updated selected files in : {perf_counter()-start_time:.3f}sec")
        return selected

    def folder_tree_double_clicked(self, index):
        folder = Path(self.folder_tree.model().filePath(index))
        self.set_root_dir(folder)

    def open_file_in_explorer(self, index):
        self.statusBar().showMessage('Opening file in explorer...')
        file = self.files[index.row()]
        Popen(f'explorer /select,"{file.path_item}"')

    def all_none_buttons(self, list_type: str, button: str):
        if list_type == 'extension':
            if button == 'all':
                self.extension_states = [2] * len(self.files)
                self.ignored_states = [0] * len(self.files)
            else:
                self.extension_states = [0] * len(self.files)
        else:
            if button == 'all':
                self.ignored_states = [2] * len(self.files)
                self.extension_states = [0] * len(self.files)
            else:
                self.ignored_states = [0] * len(self.files)
        self.selected_files = self.get_selected_files()
        self.refresh_lists()

    def set_selected_label(self):
        size = sum(file.size for file in self.selected_files)
        self.selectedfiles_label.setText(f"Selected Files : {len(self.selected_files)} ~ {size:.2f} MB")

    def refresh_lists(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.file_table.model().layoutChanged.emit()
        self.extension_list.model().layoutChanged.emit()
        self.ignored_list.model().layoutChanged.emit()
        self.set_selected_label()
        QtWidgets.QApplication.restoreOverrideCursor()

    def refresh(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.set_root_dir()
        if not self.refresh_check.isChecked():  # force set_files if 'auto refresh' is off
            self.set_files()
        QtWidgets.QApplication.restoreOverrideCursor()

    def process(self):
        selected_files = self.selected_files
        if not selected_files:
            self.statusBar().showMessage("Nothing to process.")
            return
        self.statusBar().showMessage('Processing selected files...')

        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        start_time = perf_counter()
        action = self.actionbuttons_group.checkedButton().text()
        if action == 'Delete':
            func = self.delete_files
        elif action == 'Copy':
            func = self.copy_files
        else:
            func = self.move_files

        i = 0
        self.progress_bar.setMaximum(len(selected_files))
        for _ in func():
            i += 1
            self.progress_bar.setValue(i)

        QtWidgets.QApplication.restoreOverrideCursor()
        self.statusBar().showMessage(f"Process completed in : {perf_counter()-start_time:.3f}sec")
        self._set_files()

    def delete_files(self):
        self.statusBar().showMessage('Deleting selected files...')
        result = QtWidgets.QMessageBox.warning(self, "Delete warning", "Are you sure you want to permanently delete "
                                                                       "the selected files ?",
                                               QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.Cancel)
        if result != QtWidgets.QMessageBox.Yes:
            self.statusBar().showMessage("Canceled files deletion.")
            return
        for file in self.selected_files:
            file.path_item.unlink()
            yield file

    def copy_files(self):
        self.statusBar().showMessage('Copying selected files...')
        subfolder = self.subfolder_line.text()
        for file in self.selected_files:
            subfolder_path = file.path_item.parent / subfolder
            if not subfolder_path.exists():
                subfolder_path.mkdir()
            new_path = file.path_item.parent / subfolder_path / file.path_item.name
            copy2(str(file.path_item), str(new_path))
            yield file

    def move_files(self):
        self.statusBar().showMessage('Moving selected files...')
        subfolder = self.subfolder_line.text()
        for file in self.selected_files:
            subfolder_path = file.path_item.parent / subfolder
            if not subfolder_path.exists():
                subfolder_path.mkdir()
            new_path = file.path_item.parent / subfolder_path / file.path_item.name
            move(str(file.path_item), str(new_path))
            yield file


class FileModel(QtCore.QAbstractTableModel):
    def __init__(self, ui):
        super(FileModel, self).__init__()
        self.ui = ui

    def rowCount(self, *args):
        return len(self.ui.files)

    def columnCount(self, *args):
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
                return f'{self.ui.files[row].size:.2f} MB'  # :.2f replaces round(size, 2)
        elif role == QtCore.Qt.BackgroundRole:
            if self.ui.files[index.row()] in self.ui.selected_files:
                return QtGui.QColor(62, 118, 92)

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

    def sort(self, column, order):
        self.ui.sort_files(column, order)
        self.layoutChanged.emit()


class ExtensionModel(QtCore.QAbstractListModel):
    def __init__(self, ui, list_type):
        super(ExtensionModel, self).__init__()
        self.ui = ui
        self.type = list_type

    def rowCount(self, *args):
        return len(self.ui.extensions)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            return self.ui.extensions[index.row()] or 'None'
        elif role == QtCore.Qt.CheckStateRole:
            if self.type == 'extension':
                return self.ui.extension_states[index.row()]
            else:
                return self.ui.ignored_states[index.row()]

    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.CheckStateRole:
            if self.type == 'extension':
                if value == 2:
                    self.ui.ignored_states[index.row()] = 0
                    self.ui.ignored_list.model().dataChanged.emit(index, index)
                self.ui.extension_states[index.row()] = value
            else:
                if value == 2:
                    self.ui.extension_states[index.row()] = 0
                    self.ui.extension_list.model().dataChanged.emit(index, index)
                self.ui.ignored_states[index.row()] = value
            self.dataChanged.emit(index, index)
            self.ui.selected_files = self.ui.get_selected_files()
            self.ui.file_table.model().layoutChanged.emit()
            self.ui.set_selected_label()
            return True
        return False

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable


@dataclass
class File:
    name: str
    suffix: str
    size: float
    stem: str
    path_item: Path


def get_files(path, with_subfolders=False):
    files = []
    subfolders = []
    for item in path.iterdir():
        if item.is_file():
            size = item.stat().st_size/(1024**2)
            files.append(File(item.name, item.suffix, size, item.stem, item))
        elif with_subfolders:
            subfolders.append(item)
    for item in subfolders:
        files.extend(get_files(item, with_subfolders))
    return files


if __name__ == '__main__':
    launch_ui()
