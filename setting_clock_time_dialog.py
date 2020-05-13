# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'setting_clock_time_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(252, 190)
        self.pushButton = QtWidgets.QPushButton(Dialog)
        self.pushButton.setGeometry(QtCore.QRect(80, 130, 92, 28))
        self.pushButton.setObjectName("pushButton")
        self.dateEdit = QtWidgets.QDateEdit(Dialog)
        self.dateEdit.setGeometry(QtCore.QRect(30, 30, 110, 22))
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setTimeSpec(QtCore.Qt.LocalTime)
        self.dateEdit.setObjectName("dateEdit")
        self.timeEdit = QtWidgets.QTimeEdit(Dialog)
        self.timeEdit.setGeometry(QtCore.QRect(150, 30, 71, 22))
        self.timeEdit.setObjectName("timeEdit")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.pushButton.setText(_translate("Dialog", "确定"))
        self.dateEdit.setDisplayFormat(_translate("Dialog", "yyyy/MM/dd"))
        self.timeEdit.setDisplayFormat(_translate("Dialog", "HH:mm"))

