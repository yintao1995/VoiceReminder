# !usr/bin/env python
# -*- coding:utf-8 -*-
# # @Author: Yin Tao
# @File: main.py
# @Time: 2020/05/09
# 
import sys, os
import datetime
from voice_reminder import *
from setting_clock_time_dialog import *
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QMessageBox, QListWidgetItem, \
    QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QTimer, Qt, QDate, QTime, QSize, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QColor
from record import Recorder, play_wav
import json


DATABASE_FILE = "db.json"


def get_current_time_string():
    return datetime.datetime.now().strftime("%Y-%m-%d  %H:%M")


def get_data_from_database(database_file=DATABASE_FILE):
    """
    读取文件并返回数据列表
    """
    reminder_list = []
    try:
        with open(database_file, 'r') as f:
            reminder_list = json.load(f)
            return reminder_list
    except FileNotFoundError:
        print("No such file name {}.".format(database_file))
        return reminder_list


def write_data_to_database(reminder_list, database_file=DATABASE_FILE):
    with open(database_file, 'w') as f:
        json.dump(reminder_list, f)


def save_reminder_information_to_database(clock_time_string, wav_filename, database_file=DATABASE_FILE):
    """
    将(时间串, 录音文件名)数据对追加写入对应的数据文件中
    """
    reminder_list = get_data_from_database(database_file)
    reminder_list.append([clock_time_string, wav_filename, True])
    reminder_list.sort(key=lambda x: x[0])  # 按闹钟触发时间排序
    write_data_to_database(reminder_list)


def delete_reminder_from_database(clock_time_string, wav_filename, database_file=DATABASE_FILE):
    """
    从文件中的数据列表中删除对应的(时间串, 录音文件名)数据对
    """
    reminder_list = get_data_from_database(database_file)
    for i, reminder in enumerate(reminder_list):
        if reminder[0] == clock_time_string and reminder[1] == wav_filename:
            del reminder_list[i]
            os.remove(reminder[1]+".wav")
            break
    write_data_to_database(reminder_list)


def split_into_happened_and_not_happened_ones(current_time_string: str, all_reminders_list: list):
    """
    以当前时间为准，将全部记录划分成已完成和未完成
    """
    all_reminders_list.sort(key=lambda x: x[0])
    happened = []
    not_happened = []
    for i in range(len(all_reminders_list)):
        if current_time_string >= all_reminders_list[i][0]:
            # 这里加上=，则时间到了只提示一次就被列为happened
            happened.append(all_reminders_list[i])
        else:
            not_happened.append(all_reminders_list[i])
    return happened, not_happened


class SettingTimeDialog(QDialog, Ui_Dialog):
    """
    录音之后用于设置时间的对话框。
    """

    def __init__(self, parent=None):
        super(SettingTimeDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.display_time_same_as_current_time()

    def display_time_same_as_current_time(self):
        self.dateEdit.setDate(QDate.currentDate())
        self.timeEdit.setTime(QTime.currentTime())

    def show_in_somewhere(self, x=0, y=0):
        """
        每次show()的时候显示在父窗口中间
        """
        self.show()
        self.move(x, y)


class DeleteItemSignal(QObject):
    """
    用于在QListWidgetItem与主窗口之间进行通信的自定义信号
    """
    instance = None
    signal = pyqtSignal()

    @classmethod
    def my_signal(cls):
        if cls.instance:
            return cls.instance
        else:
            obj = cls()
            cls.instance = obj
            return cls.instance

    def em(self):
        self.signal.emit()


class TimingThread(QThread):
    time_out_signal = pyqtSignal()

    def __init__(self, target_time_string='', target_sound_string=''):
        super(TimingThread, self).__init__()
        self.target_time_string = target_time_string
        self.target_sound_string = target_sound_string

    def set_time_and_audio_filename(self, _target_time_string: str, _target_sound_string: str):
        self.target_time_string = _target_time_string
        self.target_sound_string = _target_sound_string

    def run(self):
        if not self.target_time_string or not self.target_sound_string:
            return
        while True:
            current_time_string = get_current_time_string()
            print(datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
            if current_time_string < self.target_time_string:
                self.sleep(5)
            elif current_time_string == self.target_time_string:
                print("时间到！")
                play_wav("prefix.wav")
                play_wav(self.target_sound_string)
                self.time_out_signal.emit()
                # 当前待办完成后，发送信号执行主窗口的display_all_reminders_list_from_existed_database()函数刷新列表
                # 一来将刚完成的列表置为灰色，二来传递下一个待办的参数给此线程，继续计时
                break
            else:
                break


class PlayAudioThread(QThread):
    """
    播放录音的线程
    """
    def __init__(self, wav_filename=''):
        super(PlayAudioThread, self).__init__()
        self.wav_filename = wav_filename

    def set_wav_filename(self, wav_filename):
        self.wav_filename = wav_filename

    def run(self):
        play_wav(self.wav_filename)


class MyQListItem(QListWidgetItem):
    """
    自定义QListWidgetItem，Label显示待办时间，Button可删除该待办事项
    """
    item_delete_signal = pyqtSignal()

    def __init__(self, name='', parent=None):
        super(MyQListItem, self).__init__(parent)
        self.widget = QWidget()
        self.label = QLabel(name)
        self.btn = QPushButton("X")
        self.btn.setMaximumWidth(40)
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label, 4)
        self.layout.addWidget(self.btn, 1)
        self.widget.setLayout(self.layout)
        self.setSizeHint(self.widget.sizeHint())

        self.btn.clicked.connect(self.delete_this_item)

    def delete_this_item(self):
        """
        点击按钮从数据文件中删除此条待办，并触发信号，让主窗口刷新数据显示。
        """
        delete_reminder_from_database(self.label.text(), self.toolTip())
        DeleteItemSignal.my_signal().em()


class MyWidget(QWidget, Ui_Form):
    """
    主窗口
    """
    item_delete_signal = DeleteItemSignal.my_signal().signal

    def __init__(self, parent=None):
        super(MyWidget, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("VoiceReminder")
        self.pushButton.setStyleSheet("QPushButton{border-image: url(img/start.png)}")
        self.lcdNumber.setDigitCount(2)
        self.lcdNumber.setVisible(False)

        self.setting_time_dialog = SettingTimeDialog()
        self.setting_time_dialog.setWindowModality(Qt.ApplicationModal)
        self.record = Recorder()
        self.timer = QTimer()
        self.timing_thread = TimingThread()
        self.play_thread = PlayAudioThread()
        self.is_recording = False   # 用于判断当前是否正在录音

        self.display_all_reminders_list_from_existed_database()
        self.timer.timeout.connect(self.displaying_recording_time)
        self.pushButton.clicked.connect(lambda: self.start_or_stop_recording(self.is_recording))
        self.setting_time_dialog.pushButton.clicked.connect(self.set_time_from_dialog)
        self.listWidget.itemClicked.connect(self.play_corresponding_audio_file)  # itemClicked自带一个参数:item
        self.item_delete_signal.connect(self.display_all_reminders_list_from_existed_database)
        self.timing_thread.time_out_signal.connect(self.display_all_reminders_list_from_existed_database)

    def displaying_recording_time(self):
        """
        每1秒触发一次，使得LCD显示加1，作为录音时长的显示
        """
        self.lcdNumber.display(self.lcdNumber.intValue() + 1)

    def start_or_stop_recording(self, flag):
        """
        根据self.is_recording标记判断此时按下按钮是开始录音还是停止录音
        """
        if not flag:    # 开始录音
            self.lcdNumber.setVisible(True)
            self.start_recording()
            self.timer.start(1000)
        else:   # 停止录音，并显示提醒时间的设置对话框
            self.timer.stop()
            self.lcdNumber.setVisible(False)
            self.lcdNumber.display(0)
            self.stop_recording()
            self.setting_time_dialog.show_in_somewhere(
                self.pos().x() + (self.width() - self.setting_time_dialog.width()) // 2,
                self.pos().y() + (self.height() - self.setting_time_dialog.height()) // 2)
            self.setting_time_dialog.display_time_same_as_current_time()

    def start_recording(self):
        """
        开始录音
        """
        self.is_recording = True
        self.pushButton.setStyleSheet("QPushButton{border-image: url(img/stop.png)}")
        self.record.start()

    def stop_recording(self):
        """
        停止录音
        """
        self.is_recording = False
        self.pushButton.setStyleSheet("QPushButton{border-image: url(img/start.png)}")
        self.record.stop()
        self.record.save()

    def set_time_from_dialog(self):
        """
        设置时间后，将(时间串, 录音文件名)存入数据文件，并刷新窗口
        """
        date_string = self.setting_time_dialog.dateEdit.date().toString("yyyy-MM-dd")
        time_string = self.setting_time_dialog.timeEdit.time().toString("HH:mm")
        target_time_string = date_string + "  " + time_string
        self.setting_time_dialog.setVisible(False)
        save_reminder_information_to_database(target_time_string, self.record.filename)
        self.display_all_reminders_list_from_existed_database()

    def display_all_reminders_list_from_existed_database(self, database_file=DATABASE_FILE):
        """
        读取数据文件中的所有待办事项并重新显示
        """
        self.listWidget.clear()
        try:
            reminder_list = get_data_from_database(database_file)
            if not reminder_list:
                print("无语音待办提醒")
                return
            current_time_string = get_current_time_string()  # 获取当前时间，判断哪些是无效的那些是有效的
            happened, not_happened = split_into_happened_and_not_happened_ones(current_time_string, reminder_list)
            if not not_happened:
                self.timing_thread.set_time_and_audio_filename('', '')
                # 没有not_happened待办时，传递空值参数使计时线程停止
                print("所有语音待办提醒均已完成")
            else:
                self.timing_thread.set_time_and_audio_filename(not_happened[0][0], not_happened[0][1])
            self.timing_thread.start()
            not_happened_length = len(not_happened)
            for i, reminder in enumerate(not_happened + happened[::-1]):
                item = MyQListItem(name=reminder[0])
                item.setToolTip(reminder[1])
                if i >= not_happened_length:    # 已完成待办显示成灰色
                    item.label.setStyleSheet("color:#aaaaaa;")
                else:
                    item.label.setStyleSheet("color:#000000;")
                self.listWidget.addItem(item)
                self.listWidget.setItemWidget(item, item.widget)
        except FileNotFoundError:
            print("您还没有创建任何语音待办提醒")

    def play_corresponding_audio_file(self, item):
        """
        播放列表中的此item对应的语音文件
        """
        print(item.label.text(), "Voice filename:", item.toolTip())
        try:
            self.play_thread.set_wav_filename(item.toolTip())
            self.play_thread.start()
        except FileNotFoundError:
            # 如果找不到对应的语音文件，则删除此条
            msg_box = QMessageBox()
            ret = msg_box.warning(self, "Warning", "Can't find .wav file, will u want to delete it?",
                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if ret == QMessageBox.Yes:
                delete_reminder_from_database(item.label.text(), item.toolTip())
                self.display_all_reminders_list_from_existed_database()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MyWidget()
    # mw = SettingTimeDialog()
    # mw = ItemWidget()
    mw.show()
    sys.exit(app.exec_())
