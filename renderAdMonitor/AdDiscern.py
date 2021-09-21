# !/usr/bin/env python3
# -*-coding:utf-8 -*-

"""
# File       : AdDiscern.py
# Time       ：2021/9/14 11:51
# Author     ：Yooha
"""

from PyQt5 import QtCore, QtWidgets
import PyQt5
import sys
from PyQt5.QtWidgets import QMessageBox
import frida
import time
import json
import threading
from PyQt5.QtGui import QStandardItem,QStandardItemModel


# 1-监控中  2-正在加载
JS_MONITOR = 1
JS_LOAD    = 2

#***********************************************************************************
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(706, 686)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(30, 20, 61, 16))
        self.label.setObjectName("label")
        self.edt_pkgname = QtWidgets.QLineEdit(self.centralwidget)
        self.edt_pkgname.setGeometry(QtCore.QRect(90, 20, 221, 20))
        self.edt_pkgname.setObjectName("edt_pkgname")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(350, 20, 41, 16))
        self.label_2.setObjectName("label_2")
        self.edt_delaytime = QtWidgets.QLineEdit(self.centralwidget)
        self.edt_delaytime.setGeometry(QtCore.QRect(380, 20, 81, 20))
        self.edt_delaytime.setObjectName("edt_delaytime")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(470, 20, 41, 16))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(30, 60, 80, 16))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(30, 260, 80, 16))
        self.label_5.setObjectName("label_5")
        self.lst_monitor = QtWidgets.QListView(self.centralwidget)
        self.lst_monitor.setGeometry(QtCore.QRect(30, 80, 641, 171))
        self.lst_monitor.setObjectName("lst_monitor")
        self.lst_underway = QtWidgets.QListView(self.centralwidget)
        self.lst_underway.setGeometry(QtCore.QRect(30, 280, 641, 381))
        self.lst_underway.setObjectName("lst_underway")
        self.btn_start = QtWidgets.QPushButton(self.centralwidget)
        self.btn_start.setGeometry(QtCore.QRect(510, 20, 151, 23))
        self.btn_start.setObjectName("btn_start")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 706, 23))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "自渲染检测工具 1.0"))
        self.label.setText(_translate("MainWindow", "应用包名"))
        self.label_2.setText(_translate("MainWindow", "延时"))
        self.label_3.setText(_translate("MainWindow", "秒"))
        self.label_4.setText(_translate("MainWindow", "已被监控事件"))
        self.label_5.setText(_translate("MainWindow", "当前发生事件"))
        self.btn_start.setText(_translate("MainWindow", "开始监控"))


class WindowAction(PyQt5.QtWidgets.QMainWindow):
    
    def __init__(self, render:object):
        super(WindowAction, self).__init__()
        self.render:AdRender = render


    def click_start(self):
        pkgname = self.render.ui.edt_pkgname.text()
        if pkgname == '':
            QMessageBox.warning(self,"警告", '请输入包名',QMessageBox.Ok)
            return      
        delaytime = self.render.ui.edt_delaytime.text()
        if delaytime == '':
            delaytime = 30
        else:
            delaytime = int(delaytime)
        self.render.clear_list_monitor()
        self.render.clear_list_underway()
        try:
            proc = Process(pkgname)
            proc.spawn(injectJs="./resource/inject.js", delayTime=delaytime)
        except Exception as err:
            QMessageBox.critical(self, "错误", str(err), QMessageBox.Ok)
        

#***********************************************************************************
def on_message(message, data):
    """
    function:  消息回调，用于接收并处理JS中发送的流量信息
    """
    if message['type'] == 'send':
        if message['payload'][:5] == 'ad:::':
            jsonpacket = json.loads(message['payload'][5:])
            AdRender.parse(jsonpacket)
    else:
        pass

#***********************************************************************************
class Process(object):

    def __init__(self, pkgname):
        self.pid = None
        self.pkgname = pkgname
        self.session = None
        self.script = None
        self.device = frida.get_usb_device(timeout=15)
        pass


    def spawn(self, injectJs, delayTime=60):
        self.unload()
        self.pid = self.device.spawn(self.pkgname)
        self.device.resume(self.pid)

        while True: 
            try:
                # print('get session...')
                time.sleep(0.5)
                self.session = self.device.attach(self.pid)
            except:
                continue
            break

        with open(injectJs, "r", encoding='utf-8') as f:
            self.script = self.session.create_script(f.read())
        self.script.on("message", on_message) 
        self.script.load()
        self.timethread=threading.Timer(delayTime, self.export) 
        self.timethread.start()


    def export(self):
        self.script.exports.inject()


    def unload(self):
        """
        function:  释放script 和 session的资源
        """
        try:
            self.script.unload()
            self.session.detach()
        except:
            pass
#***********************************************************************************
class AdRender(object):
    def __init__(self):
        self.init()


    @classmethod
    def init(cls):
        cls.application = PyQt5.QtWidgets.QApplication(sys.argv)
        cls.ui = Ui_MainWindow()
        cls.window = WindowAction(cls)
        cls.window.setWindowIcon(PyQt5.QtGui.QIcon('./resource/icon.png'))
        cls.ui.setupUi(cls.window)
        cls.list_monitor_model = QStandardItemModel()
        cls.list_underway_model = QStandardItemModel()
        cls.setup_action()
        cls.setup_listLabel()
        cls.window.show()
        sys.exit(cls.application.exec_())


    @classmethod
    def setup_listLabel(cls):
        cls.list_monitor_model.appendRow(QStandardItem('%-30s%-50s' %('SDK', '事件')))
        cls.ui.lst_monitor.setModel(cls.list_monitor_model)
        cls.list_underway_model.appendRow(QStandardItem('%-30s%-50s' %('SDK', '事件')))
        cls.ui.lst_underway.setModel(cls.list_underway_model)


    @classmethod
    def add_list_monitor(cls, sdk, event):
        cls.list_monitor_model.appendRow(QStandardItem('%-30s%-50s' %(sdk, event)))


    @classmethod
    def clear_list_monitor(cls):
        cls.list_monitor_model.clear()
        cls.list_monitor_model.appendRow(QStandardItem('%-30s%-50s' %('SDK', '事件')))


    @classmethod
    def add_list_underway(cls, sdk, event):
        cls.list_underway_model.appendRow(QStandardItem('%-30s%-50s' %(sdk, "正在 " + event)))


    @classmethod
    def clear_list_underway(cls):
        cls.list_underway_model.clear()
        cls.list_underway_model.appendRow(QStandardItem('%-30s%-50s' %('SDK', '事件')))


    @classmethod
    def setup_action(cls):
        cls.ui.btn_start.clicked.connect(cls.window.click_start)


    @classmethod
    def parse(cls, data):
        sdk, event, status, msg = data['sdk'], data['event'], data['status'], data['msg']
        if status == JS_MONITOR:
            cls.add_list_monitor(sdk, event)
        if status == JS_LOAD:
            cls.add_list_underway(sdk, event)

#***********************************************************************************
if __name__ == '__main__':
    AdRender()


