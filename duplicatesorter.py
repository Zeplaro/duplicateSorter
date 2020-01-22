# coding: utf-8
from PyQt5 import QtWidgets, QtCore, QtGui
import sys
from os import path as ospath
from pathlib import Path
from shutil import copyfile
import subprocess
from functools import partial
from time import time
import platform


qt_refresh = QtWidgets.QApplication.processEvents


def launch_ui():
    app = QtWidgets.QApplication(sys.argv)
    ui = MainUI()
    ui.show()
    sys.exit(app.exec_())


def dark_palette():
    QtWidgets.QApplication.setStyle("Fusion")
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(43, 43, 43))
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(60, 63, 65))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(190, 190, 190))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(50, 53, 55))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor(210, 210, 210))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(60, 63, 65))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(200, 200, 200))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(80, 113, 135))
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Highlight, QtGui.QColor(80, 80, 80))
    palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.white)
    return palette


def default_palette():
    QtWidgets.QApplication.setStyle("Fusion")
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(245, 245, 245))
    return palette


class MainUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = {}
        self.ext_data = {}
        self.selected = set()
        self.folder_path = None
        self.extension_btns = []
        self.ignore_btns = []

        self.ui_layout()
        self.ui_connections()
        self.setPalette(default_palette())

        self.set_root_dir()

    def ui_layout(self):
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QtWidgets.QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setGeometry(0, 0, 1500, 800)
        self.setWindowTitle('Duplicate Sorter')
        menu_bar = QtWidgets.QMenuBar()
        self.setMenuBar(menu_bar)
        view_menu = menu_bar.addMenu('View')
        view_menu.addAction('Set default style', partial(self.setPalette, default_palette()))
        view_menu.addAction('Set dark style', partial(self.setPalette, dark_palette()))

        browse_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(browse_layout)
        self.parent_btn = QtWidgets.QToolButton()
        browse_layout.addWidget(self.parent_btn)
        self.parent_btn.setArrowType(QtCore.Qt.LeftArrow)
        self.root_path = Path(f"{ospath.expanduser('~')}/Pictures")
        self.browse_line = QtWidgets.QLineEdit(str(self.root_path))
        browse_layout.addWidget(self.browse_line)
        self.subfolders_check = QtWidgets.QCheckBox('Include subfolders')
        browse_layout.addWidget(self.subfolders_check)
        self.browse_button = QtWidgets.QPushButton('Browse')
        browse_layout.addWidget(self.browse_button)

        tree_view_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(tree_view_layout)
        main_layout.setStretchFactor(tree_view_layout, 5)
        self.folder_tree = QtWidgets.QTreeView()
        tree_view_layout.addWidget(self.folder_tree)
        folder_model = QtWidgets.QFileSystemModel()
        folder_model.setReadOnly(True)
        folder_model.setFilter(QtCore.QDir.Dirs | QtCore.QDir.NoDotAndDotDot)
        self.folder_tree.setModel(folder_model)
        self.folder_tree.setAlternatingRowColors(True)
        self.folder_tree.setAnimated(False)
        self.folder_tree.setIndentation(20)
        self.folder_tree.setSortingEnabled(True)
        self.folder_tree.setColumnHidden(1, True)
        self.folder_tree.setColumnHidden(2, True)
        self.folder_tree.setColumnHidden(3, True)
        self.folder_tree.setFixedWidth(300)
        self.folder_tree.setColumnWidth(0, 200)
        self.folder_tree.sortByColumn(0, QtCore.Qt.AscendingOrder)

        self.view = QtWidgets.QTreeWidget()
        tree_view_layout.addWidget(self.view)
        self.view.setAlternatingRowColors(True)
        self.view.setSortingEnabled(True)
        self.view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.view.setColumnCount(3)
        self.view.setHeaderLabels(('Name', 'Type', 'Size'))
        self.view.setColumnWidth(0, 400)
        self.view.setIndentation(4)
        self.view.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.view.setMinimumHeight(300)

        tools_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(tools_layout)
        main_layout.setStretchFactor(tools_layout, 3)

        extension_layout = QtWidgets.QVBoxLayout()
        tools_layout.addLayout(extension_layout)
        extension_box = QtWidgets.QGroupBox('Extensions')
        extension_box.setFixedWidth(200)
        extension_box.setMaximumHeight(300)
        extension_layout.addWidget(extension_box)
        extension_box_layout = QtWidgets.QVBoxLayout()
        extension_box_layout.setSpacing(0)
        extension_box_layout.setContentsMargins(0, 0, 0, 0)
        extension_box.setLayout(extension_box_layout)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        extension_box_layout.addWidget(scroll_area)
        scroll_container = QtWidgets.QWidget()
        scroll_area.setWidget(scroll_container)
        self.sub_extension_layout = QtWidgets.QVBoxLayout()
        scroll_container.setLayout(self.sub_extension_layout)

        extension_btn_layout = QtWidgets.QHBoxLayout()
        extension_layout.addLayout(extension_btn_layout)
        self.all_extensions_button = QtWidgets.QPushButton('All')
        extension_btn_layout.addWidget(self.all_extensions_button)
        self.no_extensions_button = QtWidgets.QPushButton('None')
        extension_btn_layout.addWidget(self.no_extensions_button)

        ignored_layout = QtWidgets.QVBoxLayout()
        tools_layout.addLayout(ignored_layout)
        ingnored_box = QtWidgets.QGroupBox('Ignored')
        ingnored_box.setFixedWidth(200)
        ingnored_box.setMaximumHeight(300)
        ignored_layout.addWidget(ingnored_box)
        ignored_box_layout = QtWidgets.QVBoxLayout()
        ignored_box_layout.setSpacing(0)
        ignored_box_layout.setContentsMargins(0, 0, 0, 0)
        ingnored_box.setLayout(ignored_box_layout)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        ignored_box_layout.addWidget(scroll_area)
        scroll_container = QtWidgets.QWidget()
        scroll_area.setWidget(scroll_container)
        self.sub_ignored_layout = QtWidgets.QVBoxLayout()
        scroll_container.setLayout(self.sub_ignored_layout)

        ignore_btn_layout = QtWidgets.QHBoxLayout()
        ignored_layout.addLayout(ignore_btn_layout)
        self.all_ignore_button = QtWidgets.QPushButton('All')
        ignore_btn_layout.addWidget(self.all_ignore_button)
        self.no_ignore_button = QtWidgets.QPushButton('None')
        ignore_btn_layout.addWidget(self.no_ignore_button)

        action_box = QtWidgets.QGroupBox('Actions')
        tools_layout.addWidget(action_box)
        action_layout = QtWidgets.QVBoxLayout()
        action_box.setLayout(action_layout)
        action_box.setFixedWidth(200)
        self.action_button_group = QtWidgets.QButtonGroup()
        for action in ('Delete', 'Copy', 'Move'):
            action_button = QtWidgets.QRadioButton(action)
            self.action_button_group.addButton(action_button)
            action_layout.addWidget(action_button)
            action_button.setChecked(True)
        self.move_line = QtWidgets.QLineEdit('subfolder')
        action_layout.addWidget(self.move_line)
        self.move_line.setFixedWidth(150)

        stats_layout = QtWidgets.QVBoxLayout()
        tools_layout.addLayout(stats_layout)
        self.total_label = QtWidgets.QLabel('Total files : 0')
        self.total_label.setMargin(10)
        stats_layout.addWidget(self.total_label)
        self.selected_label = QtWidgets.QLabel('Selected files : 0 ~ 0 MB')
        self.selected_label.setMargin(10)
        stats_layout.addWidget(self.selected_label)

        process_layout = QtWidgets.QVBoxLayout()
        process_layout.setAlignment(QtCore.Qt.AlignRight)
        tools_layout.addLayout(process_layout)
        self.refresh_checkbox = QtWidgets.QCheckBox('Auto refresh')
        self.refresh_checkbox.setCheckState(2)
        process_layout.addWidget(self.refresh_checkbox)
        self.refresh_button = QtWidgets.QPushButton('Refresh')
        self.refresh_button.setFixedHeight(35)
        self.refresh_button.setFixedWidth(150)
        process_layout.addWidget(self.refresh_button)
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFixedHeight(20)
        process_layout.addWidget(separator)
        self.process_button = QtWidgets.QPushButton('Process')
        self.process_button.setFixedHeight(50)
        self.process_button.setFixedWidth(150)
        process_layout.addWidget(self.process_button)

        self.process_bar = QtWidgets.QProgressBar()
        main_layout.addWidget(self.process_bar)

    def ui_connections(self):
        self.folder_tree.clicked.connect(self.refresh_view)
        self.folder_tree.doubleClicked.connect(self.set_children_folder)
        self.browse_button.clicked.connect(self.browse)
        self.browse_line.editingFinished.connect(self.set_root_dir)
        self.view.doubleClicked.connect(self.open_path)
        self.no_extensions_button.clicked.connect(partial(self.check_extensions, 0))
        self.all_extensions_button.clicked.connect(partial(self.check_extensions, 2))
        self.no_ignore_button.clicked.connect(partial(self.check_ignore, 0))
        self.all_ignore_button.clicked.connect(partial(self.check_ignore, 2))
        self.process_button.clicked.connect(self.process)
        self.parent_btn.clicked.connect(self.set_parent_folder)
        self.subfolders_check.clicked.connect(self.set_root_dir)
        self.refresh_button.clicked.connect(self.populate_view)

    def refresh_view(self):
        if self.refresh_checkbox.isChecked():
            self.populate_view()

    def refresh_highlight(self):
        if self.refresh_checkbox.isChecked():
            self.highlight()

    def set_root_dir(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.browse_line.setText(self.browse_line.text().replace('\\', '/'))
        path = self.browse_line.text()
        self.root_path = Path(path)
        if self.root_path.exists():
            model = self.folder_tree.model()
            model.setRootPath(path)
            self.folder_tree.setRootIndex(model.index(path))
        self.refresh_view()
        QtWidgets.QApplication.restoreOverrideCursor()

    def progress(self):
        prog = QtWidgets.QDialog(parent=self)
        prog.setWindowTitle('Populating')
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        prog.setLayout(layout)
        label = QtWidgets.QLabel()
        layout.addWidget(label)
        return prog, label

    def populate_view(self, *args):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        for file in self.selected:
            for i in range(3):
                self.data[file]['item'].setBackground(i, QtGui.QColor(1, 1, 1, 1))
        self.selected = set()
        self.view.clear()
        data = {}
        ext_data = {}
        path = self.folder_tree.model().filePath(self.folder_tree.currentIndex())
        if path:
            self.folder_path = Path(path)
        else:
            self.folder_path = self.root_path
        if self.subfolders_check.isChecked():
            func = self.folder_path.rglob
        else:
            func = self.folder_path.glob

        for file in func('*.*'):
            item = QtWidgets.QTreeWidgetItem()
            ext = file.suffix
            size = ospath.getsize(str(file)) / (1024 * 1024)
            data[str(file)] = {'file': file,
                                     'name': file.stem.lower(),
                                     'item': item,
                                     'ext': ext,
                                     'size': size,
                                     }
            if ext not in ext_data:
                ext_data[ext] = set()
            ext_data[ext].add(str(file))

            item.setText(0, file.name)
            item.setText(1, ext)
            item.setText(2, str(round(size, 3))+' MB')
            item.setTextAlignment(2, QtCore.Qt.AlignRight)
            self.view.addTopLevelItem(item)
            item.path = file

        counts = (len(ext_data[ext]) for ext in ext_data)
        self.total_label.setText(f'Total files : {sum(counts)}')

        self.ext_data = ext_data
        self.data = data
        self.populate_extensions()
        QtWidgets.QApplication.restoreOverrideCursor()
        self.highlight()

    def populate_extensions(self):
        checked = {}
        ignored = {}
        for item in self.extension_btns:
            if item.isChecked():
                checked[item.text()] = 2
            self.sub_extension_layout.removeWidget(item)
            item.hide()
            del item
        for item in self.ignore_btns:
            if item.isChecked():
                ignored[item.text()] = 2
            self.sub_ignored_layout.removeWidget(item)
            item.hide()
            del item

        extension_btns = []
        ignore_btns = []
        for extension in sorted(self.ext_data, key=lambda x: x.lower()):
            ext_btn = QtWidgets.QCheckBox(extension)
            extension_btns.append(ext_btn)
            self.sub_extension_layout.addWidget(ext_btn)
            ext_btn.setCheckState(checked.get(extension, False))
            ext_btn.clicked.connect(self.refresh_highlight)

            ignore_btn = QtWidgets.QCheckBox(extension)
            ignore_btns.append(ignore_btn)
            self.sub_ignored_layout.addWidget(ignore_btn)
            ignore_btn.setCheckState(ignored.get(extension, False))
            ignore_btn.clicked.connect(self.refresh_highlight)
            ignore_btn.clicked.connect(partial(self.lock_extension, ext_btn))

        self.extension_btns = extension_btns
        self.ignore_btns = ignore_btns

    def highlight(self, *args):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        for file in self.selected:
            for i in range(3):
                self.data[file]['item'].setBackground(i, QtGui.QColor(1, 1, 1, 1))
        selected = set()
        checked_exts = set()
        unchecked_exts = set()
        for ext_btn, ignore_btn in zip(self.extension_btns, self.ignore_btns):
            if ext_btn.isChecked():
                checked_exts.add(ext_btn.text())
            else:
                if not ignore_btn.isChecked():
                    unchecked_exts.add(ext_btn.text())

        size = 0.0
        data = self.data
        for ext in checked_exts:
            for checked_file in self.ext_data[ext]:
                skip = False
                name = data[checked_file]['name']
                for unchecked_ext in unchecked_exts:
                    for file in self.ext_data[unchecked_ext]:
                        if self.data[file]['name'] == name:
                            selected.add(checked_file)
                            item = self.data[checked_file]['item']
                            for i in range(3):
                                item.setBackground(i, QtGui.QColor(255, 50, 90, 60))
                            size += self.data[checked_file]['size']
                            skip = True
                            continue
                    if skip:
                        continue

        disp_size = round(size, 2) if size < 1024 else round(size/1024, 2)
        self.selected_label.setText(f"Selected files : {len(selected)} ~ {disp_size} {'MB' if size < 1024 else 'GB'}")
        self.selected = selected
        QtWidgets.QApplication.restoreOverrideCursor()

    def set_parent_folder(self):
        self.browse_line.setText(str(self.root_path.parent))
        self.set_root_dir()

    def set_children_folder(self, index):
        if index:
            self.browse_line.setText(self.folder_tree.model().filePath(index))
            self.set_root_dir()

    def check_extensions(self, state):
        for ext in self.extension_btns:
            ext.setCheckState(state)
        self.refresh_highlight()

    def check_ignore(self, state):
        for i in self.ignore_btns:
            i.setCheckState(state)
        self.refresh_highlight()

    @staticmethod
    def lock_extension(ext_btn, state):
        if not state:
            ext_btn.setEnabled(True)
        else:
            ext_btn.setChecked(False)
            ext_btn.setEnabled(False)

    def browse(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(directory=self.browse_line.text())
        self.browse_line.setText(path)
        self.set_root_dir()

    def open_path(self, index):
        print('Opening in explorer')
        item = self.view.itemFromIndex(index)
        if platform.system() == "Windows":
            subprocess.Popen(f'explorer /select,"{item.path}"')
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", item.path])
        else:
            subprocess.Popen(["xdg-open", item.path])

    def process(self):
        if not self.selected:
            print("Nothing to process.")
            return
        print('Processing')
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        current_time = time()
        action = self.action_button_group.checkedButton().text()
        if action == 'Move':
            self.move_files()
        elif action == 'Delete':
            self.delete_files()
        else:
            self.copy_files()
        self.populate_view()
        QtWidgets.QApplication.restoreOverrideCursor()
        print(f"Process completed in : {round(time()-current_time, 3)}sec")

    def move_files(self):
        print('Moving files')
        subfolder = self.move_line.text()
        self.process_bar.setMaximum(len(self.selected))
        for i, file in enumerate(self.selected):
            file = Path(file)
            new_root = file.parent / subfolder
            if not new_root.exists():
                new_root.mkdir()
            file.replace(new_root / file.name)
            self.process_bar.setValue(i + 1)

    def delete_files(self):
        print('Deleting files')
        result = QtWidgets.QMessageBox.warning(self, "Delete warning", "Are you sure you want to permanently delete "
                                                                       "the selected files ?",
                                               QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.Cancel)
        if result != QtWidgets.QMessageBox.Yes:
            print("Canceled.")
            return
        self.process_bar.setMaximum(len(self.selected))
        for i, file in enumerate(self.selected):
            file = Path(file)
            if file.exists():
                file.unlink()
            self.process_bar.setValue(i + 1)

    def copy_files(self):
        print('Copying files')
        subfolder = self.move_line.text()
        self.process_bar.setMaximum(len(self.selected))
        for i, file in enumerate(self.selected):
            file = Path(file)
            new_root = file.parent / subfolder
            if not new_root.exists():
                new_root.mkdir()
            new_path = new_root / file.name
            copyfile(file, new_path)
            self.process_bar.setValue(i + 1)


if __name__ == '__main__':
    launch_ui()
