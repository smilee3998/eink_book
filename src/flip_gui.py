# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'flip.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1800, 1000)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.right_page = QtWidgets.QLabel(self.centralwidget)
        self.right_page.setGeometry(QtCore.QRect(870, 0, 850, 800))
        self.right_page.setText("")
        self.right_page.setScaledContents(True)
        self.right_page.setObjectName("right_page")
        self.left_page = QtWidgets.QLabel(self.centralwidget)
        self.left_page.setGeometry(QtCore.QRect(30, 0, 850, 800))
        self.left_page.setText("")
        self.left_page.setScaledContents(True)
        self.left_page.setObjectName("left_page")
        self.next_page_button = QtWidgets.QPushButton(self.centralwidget)
        self.next_page_button.setGeometry(QtCore.QRect(1400, 880, 271, 61))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.next_page_button.setFont(font)
        self.next_page_button.setObjectName("next_page_button")
        self.previous_page_button = QtWidgets.QPushButton(self.centralwidget)
        self.previous_page_button.setGeometry(QtCore.QRect(50, 880, 271, 61))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.previous_page_button.setFont(font)
        self.previous_page_button.setObjectName("previous_page_button")
        self.start_button = QtWidgets.QPushButton(self.centralwidget)
        self.start_button.setGeometry(QtCore.QRect(850, 930, 80, 23))
        self.start_button.setObjectName("start_button")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1800, 20))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.next_page_button.setText(_translate("MainWindow", "Next Page"))
        self.previous_page_button.setText(_translate("MainWindow", "Previous page"))
        self.start_button.setText(_translate("MainWindow", "start"))
