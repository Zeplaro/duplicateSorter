#!/usr/bin/env python3
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
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor(230, 230, 230))
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
        self.folder_path = None

        self.ui_layout()
        # self.ui_connections()
        self.setPalette(dark_palette())

    def ui_layout(self):
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.setCentralWidget(main_splitter)
        self.setGeometry(0, 0, 1500, 800)
        self.setWindowTitle('Duplicate Sorter')
        menu_bar = QtWidgets.QMenuBar()
        self.setMenuBar(menu_bar)
        view_menu = menu_bar.addMenu('View')
        view_menu.addAction('Set default style', partial(self.setPalette, default_palette()))
        view_menu.addAction('Set dark style', partial(self.setPalette, dark_palette()))

        top_widget = QtWidgets.QWidget()
        main_splitter.addWidget(top_widget)
        top_layout = QtWidgets.QVBoxLayout()
        top_widget.setLayout(top_layout)

        browse_layout = QtWidgets.QHBoxLayout()
        top_layout.addLayout(browse_layout)
        self.parent_btn = QtWidgets.QToolButton()
        browse_layout.addWidget(self.parent_btn)
        self.parent_btn.setArrowType(QtCore.Qt.LeftArrow)
        self.root_path = Path(f"{ospath.expanduser('~')}/Pictures")
        self.root_path = Path(f"C:/Users/robin/Photos")
        self.browse_line = QtWidgets.QLineEdit(str(self.root_path))
        browse_layout.addWidget(self.browse_line)
        self.subfolders_check = QtWidgets.QCheckBox('Include subfolders')
        browse_layout.addWidget(self.subfolders_check)
        self.browse_button = QtWidgets.QPushButton('Browse')
        browse_layout.addWidget(self.browse_button)

        tree_view_layout = QtWidgets.QHBoxLayout()
        top_layout.addLayout(tree_view_layout)
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

        self.view = QtWidgets.QTreeView()
        tree_view_layout.addWidget(self.view)
        model = PicModel()
        self.view.setModel(model)
        self.view.setRootIndex(model.index(model.path))

        bottom_widget = QtWidgets.QWidget()
        main_splitter.addWidget(bottom_widget)
        bottom_layout = QtWidgets.QVBoxLayout()
        bottom_widget.setLayout(bottom_layout)

        tools_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addLayout(tools_layout)

        extension_layout = QtWidgets.QVBoxLayout()
        tools_layout.addLayout(extension_layout)
        extension_box = QtWidgets.QGroupBox('Extensions')
        extension_box.setFixedWidth(200)
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
        self.move_line.setFixedWidth(175)

        stats_layout = QtWidgets.QVBoxLayout()
        tools_layout.addLayout(stats_layout)
        self.total_label = QtWidgets.QLabel('Total files : 0')
        self.total_label.setMargin(20)
        stats_layout.addWidget(self.total_label)
        self.selected_label = QtWidgets.QLabel('Selected files : 0 ~ 0 MB')
        self.selected_label.setMargin(20)
        stats_layout.addWidget(self.selected_label)

        process_layout = QtWidgets.QVBoxLayout()
        tools_layout.addLayout(process_layout)
        self.refresh_checkbox = QtWidgets.QCheckBox('Auto refresh')
        self.refresh_checkbox.setCheckState(2)
        self.refresh_checkbox.setFixedHeight(20)
        process_layout.addWidget(self.refresh_checkbox)
        self.refresh_button = QtWidgets.QPushButton('Refresh')
        self.refresh_button.setFixedHeight(35)
        self.refresh_button.setFixedWidth(150)
        process_layout.addWidget(self.refresh_button)
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setStyleSheet("color: rgba(0, 0, 0, 0.2);")
        separator.setLineWidth(1)
        separator.setFixedHeight(20)
        process_layout.addWidget(separator)
        self.process_button = QtWidgets.QPushButton('Process')
        self.process_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        self.process_button.setMinimumHeight(50)
        self.process_button.setFixedWidth(150)
        process_layout.addWidget(self.process_button)

        self.process_bar = QtWidgets.QProgressBar()
        bottom_layout.addWidget(self.process_bar)


class PicModel(QtWidgets.QFileSystemModel):

    def __init__(self):
        super(PicModel, self).__init__()
        self.path = 'D:\Robin\Photos\plop'
        self.setFilter(QtCore.QDir.Files)
        self.setRootPath(self.path)


if __name__ == '__main__':
    launch_ui()
