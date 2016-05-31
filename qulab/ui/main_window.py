# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui

def button(text, layout, callback, parent=None):
    btn = QtGui.QPushButton(text, parent=parent)
    btn.clicked.connect(callback)
    layout.addWidget(btn)
    return btn

class MainWindow(QtGui.QMainWindow):
    def __init__(self, app):
        super(MainWindow, self).__init__()
        self.app = app
        self.UI()

    def UI(self):
        self.centralwidget = QtGui.QWidget(self)
        self.layout = QtGui.QVBoxLayout(self.centralwidget)
        self.layout.addWidget(self.BaseUI())
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle(u'%s (QuLab %s)'%(self.app.__title__, self.app.__version__))

    def BaseUI(self):
        group = QtGui.QGroupBox(self)

        gp1 = QtGui.QGroupBox("Data Base", self)
        layout = QtGui.QHBoxLayout(gp1)
        layout.addWidget(QtGui.QLabel("Base Dir", parent=self))
        self.baseDir = QtGui.QLineEdit(self.app.main_cfg['Basic:path'], parent=self)
        btn = QtGui.QPushButton(u'Choose', parent=self)
        btn.clicked.connect(self.choose_base_dir)
        layout.addWidget(self.baseDir)
        layout.addWidget(btn)

        gp2 = QtGui.QGroupBox("Actions", self)
        layout = QtGui.QVBoxLayout(gp2)
        l1 = QtGui.QHBoxLayout()
        self.start_btn = button('Start',      l1, self.start)
        self.pause_btn = button('Pause',      l1, self.paused)
        self.ended_btn = button('Interrupt',  l1, self.interrupt)
        self.ended_btn.setEnabled(False)
        layout.addLayout(l1)
        l2 = QtGui.QHBoxLayout()
        self.hide_show_btn = button('Hide',  l2, self.hide_show)
        self.hide_show_btn.setEnabled(False)
        self.load_btn = button('Load',       l2, self.load_data)
        self.anal_btn = button('Analyse',    l2, self.analyse)
        layout.addLayout(l2)

        gp3 = QtGui.QGroupBox(self)
        self.user   = QtGui.QLineEdit(self.app.history.get("User", "default user"), parent=self)
        self.sample = QtGui.QLineEdit(self.app.history.get("Sample ID", "default"), parent=self)
        self.notes  = QtGui.QTextEdit(parent=self)
        layout1 = QtGui.QHBoxLayout()
        layout2 = QtGui.QHBoxLayout()
        layout3 = QtGui.QHBoxLayout()
        layout1.addWidget(QtGui.QLabel("User Name", parent=self))
        layout1.addWidget(self.user)
        layout2.addWidget(QtGui.QLabel("Sample ID", parent=self))
        layout2.addWidget(self.sample)
        layout3.addWidget(QtGui.QLabel("Notes    ", parent=self))
        layout3.addWidget(self.notes)
        layout = QtGui.QVBoxLayout(gp3)
        layout.addLayout(layout1)
        layout.addLayout(layout2)
        layout.addLayout(layout3)

        layout = QtGui.QHBoxLayout(group)
        ll = QtGui.QVBoxLayout()
        lr = QtGui.QVBoxLayout()
        ll.addWidget(gp1)
        ll.addWidget(gp2)
        lr.addWidget(gp3)
        layout.addLayout(lr)
        layout.addLayout(ll)

        return group

    def choose_base_dir(self):
        dir_name = QtGui.QFileDialog.getExistingDirectory(None, "Directory", self.baseDir.text())
        self.baseDir.setText(dir_name)
        self.app.database = DataBase(str(dir_name))

    @QtCore.pyqtSlot()
    def start(self):
        class Foo(QtCore.QThread):
            app = None
            started = QtCore.pyqtSignal()
            finished = QtCore.pyqtSignal()
            def run(self):
                self.started.emit()
                self.app.work()
                self.finished.emit()

        self.app.set_parameters()
        self.app.plot_manager.init()
        self.foo = Foo()
        self.foo.app = self.app
        self.foo.started.connect(self.on_work_start)
        self.foo.finished.connect(self.on_work_finished)
        self.foo.start()
        #self.app.plot_manager.show_all()

    @QtCore.pyqtSlot()
    def on_work_start(self):
        self.start_btn.setEnabled(False)
        self.ended_btn.setEnabled(True)
        self.hide_show_btn.setEnabled(True)

    @QtCore.pyqtSlot()
    def on_work_finished(self):
        self.start_btn.setEnabled(True)
        self.ended_btn.setEnabled(False)

    @QtCore.pyqtSlot()
    def on_proccess(self):
        pass

    def update(self):
        pass

    @QtCore.pyqtSlot()
    def paused(self):
        if str(self.pause_btn.text()) == "Pause":
            if self.app != None:
                self.app.paused(True)
            self.pause_btn.setText("Continue")
        elif str(self.pause_btn.text()) == "Continue":
            if self.app != None:
                self.app.paused(False)
            self.pause_btn.setText("Pause")

    # TODO: 设计使其终止后还能正常重启
    @QtCore.pyqtSlot()
    def interrupt(self):
        pass

    @QtCore.pyqtSlot()
    def hide_show(self):
        if str(self.hide_show_btn.text()) == "Hide":
            if self.app != None:
                self.app.plot_manager.hide_all()
            self.hide_show_btn.setText("Show")
        elif str(self.hide_show_btn.text()) == "Show":
            if self.app != None:
                self.app.plot_manager.show_all()
            self.hide_show_btn.setText("Hide")

    @QtCore.pyqtSlot()
    def load_data(self):
        fileName = QtGui.QFileDialog.getOpenFileName(None, "Open File", "D:\\", "All files (*.*)")
        self.app.data_manager.load_data(str(fileName))
        self.app.plot_manager.init()
        self.app.plot_manager.show_all()

    @QtCore.pyqtSlot()
    def analyse(self):
        pass
