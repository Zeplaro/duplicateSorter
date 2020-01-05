from PyQt5 import QtWidgets, QtCore, QtGui
import sys
from os import path as ospath
from pathlib import Path
from shutil import copyfile
import subprocess
from functools import partial
from time import time


def launch_ui():
    app = QtWidgets.QApplication(sys.argv)
    ui = MainUI()
    ui.show()
    sys.exit(app.exec_())


class MainUI(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.data = {}
        self.selected = []
        self.folder_path = None
        self.extension_btns = []
        self.ignore_btns = []

        self.ui_layout()
        self.ui_connections()

        self.set_root_dir()

    def ui_layout(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        self.setGeometry(0, 0, 1500, 800)
        self.setWindowTitle('Duplicate Sorter')

        browse_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(browse_layout)
        self.parent_btn = QtWidgets.QToolButton()
        browse_layout.addWidget(self.parent_btn)
        self.parent_btn.setArrowType(QtCore.Qt.LeftArrow)
        self.root_path = Path(f"{ospath.expanduser('~')}/Pictures")
        self.root_path = Path(f"D:/Robin/Pictures/Photo")
        self.browse_line = QtWidgets.QLineEdit(str(self.root_path))
        browse_layout.addWidget(self.browse_line)
        self.subfolders_check = QtWidgets.QCheckBox('Include subfolders')
        browse_layout.addWidget(self.subfolders_check)
        self.browse_button = QtWidgets.QPushButton('Browse')
        browse_layout.addWidget(self.browse_button)

        tree_view_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(tree_view_layout)
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
        self.view.setColumnCount(4)
        self.view.setHeaderLabels(('Name', 'Type', 'Size', ''))
        self.view.setColumnWidth(0, 400)
        self.view.setIndentation(4)
        self.view.sortByColumn(0, QtCore.Qt.AscendingOrder)

        tools_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(tools_layout)

        extension_box = QtWidgets.QGroupBox('Extensions')
        tools_layout.addWidget(extension_box)
        self.extension_layout = QtWidgets.QVBoxLayout()
        extension_box.setLayout(self.extension_layout)
        extension_box.setFixedWidth(200)
        extension_btn_layout = QtWidgets.QHBoxLayout()
        self.extension_layout.addLayout(extension_btn_layout)
        self.all_extensions_button = QtWidgets.QPushButton('All')
        extension_btn_layout.addWidget(self.all_extensions_button)
        self.no_extensions_button = QtWidgets.QPushButton('None')
        extension_btn_layout.addWidget(self.no_extensions_button)

        ignore_box = QtWidgets.QGroupBox('Ignore')
        tools_layout.addWidget(ignore_box)
        self.ignore_layout = QtWidgets.QVBoxLayout()
        ignore_box.setLayout(self.ignore_layout)
        ignore_box.setFixedWidth(200)
        ignore_btn_layout = QtWidgets.QHBoxLayout()
        self.ignore_layout.addLayout(ignore_btn_layout)
        self.all_ignore_button = QtWidgets.QPushButton('All')
        ignore_btn_layout.addWidget(self.all_ignore_button)
        self.no_ignore_button = QtWidgets.QPushButton('None')
        ignore_btn_layout.addWidget(self.no_ignore_button)

        action_box = QtWidgets.QGroupBox('Action')
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
        stats_layout.addWidget(self.total_label)
        self.selected_label = QtWidgets.QLabel('Selected files : 0 ; o MB')
        stats_layout.addWidget(self.selected_label)
        self.type_label = QtWidgets.QLabel('File types :')
        stats_layout.addWidget(self.type_label)

        process_layout = QtWidgets.QVBoxLayout()
        process_layout.setAlignment(QtCore.Qt.AlignRight)
        tools_layout.addLayout(process_layout)
        self.process_button = QtWidgets.QPushButton('Process')
        self.process_button.setFixedHeight(50)
        self.process_button.setFixedWidth(100)
        process_layout.addWidget(self.process_button)

        self.progress = QtWidgets.QProgressBar()
        main_layout.addWidget(self.progress)

    def ui_connections(self):
        self.folder_tree.clicked.connect(self.populate_view)
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

    def set_root_dir(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.browse_line.setText(self.browse_line.text().replace('\\', '/'))
        path = self.browse_line.text()
        self.root_path = Path(path)
        if self.root_path.exists():
            model = self.folder_tree.model()
            model.setRootPath(path)
            self.folder_tree.setRootIndex(model.index(path))
        self.populate_view()
        QtWidgets.QApplication.restoreOverrideCursor()

    def populate_view(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        checked_ext = [x.text() for x in self.extension_btns if x.isChecked()]
        checked_ignore = [x.text() for x in self.ignore_btns if x.isChecked()]
        self.view.clear()
        self.data = {}
        index = self.folder_tree.currentIndex()
        path = self.folder_tree.model().filePath(index)
        if path:
            self.folder_path = Path(path)
        else:
            self.folder_path = self.root_path
        self.file_extensions = {}
        num_files = 0
        if self.subfolders_check.isChecked():
            func = self.folder_path.rglob
        else:
            func = self.folder_path.glob
        for file in func('*.*'):
            item = QtWidgets.QTreeWidgetItem()
            size = ospath.getsize(str(file)) / (1024 * 1024)
            self.data[file] = {'name': file.stem.lower(),
                               'ext': file.suffix,
                               'item': item,
                               'size': size,
                               }
            self.file_extensions[file.suffix] = self.file_extensions.get(file.suffix, 0) + 1
            item.setText(0, file.name)
            item.setText(1, file.suffix)
            item.setText(2, str(round(size))+' MB')
            item.setTextAlignment(2, QtCore.Qt.AlignRight)
            self.view.addTopLevelItem(item)
            item.path = file
            num_files += 1
        self.total_label.setText(f'Total files : {num_files}')
        ext_count_string = ''
        sorted_extentions = sorted([(ext, num) for ext, num in self.file_extensions.items()], key=lambda x: x[0].lower())
        for i, (ext, num) in enumerate(sorted_extentions):
            ext_count_string += f'{ext} :    {num}\n                 '
        self.type_label.setText(f'File types : {ext_count_string}')
        self.populate_extensions()
        for i in self.extension_btns:
            if i.text() in checked_ext:
                i.setCheckState(2)
        for i in self.ignore_btns:
            if i.text() in checked_ignore:
                i.setCheckState(2)
        QtWidgets.QApplication.restoreOverrideCursor()
        self.highlight()

    def highlight(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.selected = {}
        ignored_extensions = tuple(x.text() for x in self.ignore_btns if x.isChecked())
        checked_extensions = tuple(x.text() for x in self.extension_btns if x.isChecked())
        new_data = {}
        for file in self.data:
            if not self.data[file]['ext'] in ignored_extensions:
                new_data[file] = self.data[file]
            else:
                for i in range(4):
                    self.data[file]['item'].setBackground(i, QtGui.QColor(1, 1, 1, 1))
        file_names = tuple(new_data[file]['name'] for file in new_data)
        count = 0
        count_data = {}
        size = 0.0
        for file in new_data:
            name = new_data[file]['name']
            if name in count_data:
                occur = count_data[name]
            else:
                occur = count_data[name] = file_names.count(name)
            if occur > 1 and new_data[file]['ext'] in checked_extensions:
                for i in range(4):
                    new_data[file]['item'].setBackground(i, QtGui.QColor(255, 0, 0, 50))
                self.selected[file] = new_data[file]
                size += new_data[file]['size']
                count += 1
            else:
                for i in range(4):
                    self.data[file]['item'].setBackground(i, QtGui.QColor(1, 1, 1, 1))
        disp_size = round(size, 2) if size < 1024 else round(size/1024, 2)
        self.selected_label.setText(f"Selected files : {count} ; {disp_size} {'MB' if size < 1024 else 'GB'}")
        QtWidgets.QApplication.restoreOverrideCursor()

    def populate_extensions(self):
        for item in self.extension_btns:
            self.extension_layout.removeWidget(item)
            item.hide()
            del item
        for item in self.ignore_btns:
            self.ignore_layout.removeWidget(item)
            item.hide()
            del item
        self.extension_btns = []
        self.ignore_btns = []
        for extension in sorted([ext for ext in self.file_extensions], key=lambda x: x.lower()):
            if extension:
                ext_btn = QtWidgets.QCheckBox(extension)
                self.extension_btns.append(ext_btn)
                self.extension_layout.insertWidget(self.ignore_layout.count()-1, ext_btn)
                ext_btn.stateChanged.connect(self.highlight)
                ignore_btn = QtWidgets.QCheckBox(extension)
                self.ignore_btns.append(ignore_btn)
                self.ignore_layout.insertWidget(self.ignore_layout.count()-1, ignore_btn)
                ignore_btn.stateChanged.connect(self.highlight)
                ignore_btn.stateChanged.connect(partial(self.lock_extension, ext_btn))

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

    def check_ignore(self, state):
        for i in self.ignore_btns:
            i.setCheckState(state)

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
        print('Opening in windows explorer')
        item = self.view.itemFromIndex(index)
        subprocess.Popen(f'explorer /select,"{item.path}"')

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
        self.progress.setMaximum(len(self.selected))
        for i, file in enumerate(self.selected):
            new_root = file.parent / subfolder
            if not new_root.exists():
                new_root.mkdir()
            file.replace(new_root / file.name)
            self.progress.setValue(i+1)

    def delete_files(self):
        print('Deleting files')
        result = QtWidgets.QMessageBox.warning(self, "Delete warning", "Are you sure you want to permanently delete "
                                                                       "the selected files ?",
                                               QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.Cancel)
        if result != QtWidgets.QMessageBox.Yes:
            print("Canceled.")
            return
        self.progress.setMaximum(len(self.selected))
        for i, file in enumerate(self.selected):
            if file.exists():
                file.unlink()
            self.progress.setValue(i+1)

    def copy_files(self):
        print('Copying files')
        subfolder = self.move_line.text()
        self.progress.setMaximum(len(self.selected))
        for i, file in enumerate(self.selected):
            new_root = file.parent / subfolder
            if not new_root.exists():
                new_root.mkdir()
            new_path = new_root / file.name
            copyfile(file, new_path)
            self.progress.setValue(i+1)


if __name__ == '__main__':
    launch_ui()
