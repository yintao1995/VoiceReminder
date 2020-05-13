# !usr/bin/env python
# -*- coding:utf-8 -*-
# # @Author: Yin Tao
# @File: record.py
# @Time: 2020/05/08
# 

import pyaudio
import wave
import time
import threading


class Recorder(object):
    def __init__(self, chunk=1024, channels=1, rate=8000):
        self.chunk = chunk
        self.format = pyaudio.paInt16
        self.channels = channels
        self.rate = rate
        self.filename = "test"
        self.continue_flag = True
        self.frames = []

    def start(self):
        # 单独一个线程录音
        t = threading.Thread(target=self.recording, args=())
        t.start()

    def recording(self):
        self.continue_flag = True
        self.frames = []
        p = pyaudio.PyAudio()
        stream = p.open(format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.chunk)
        while self.continue_flag:
            data = stream.read(self.chunk)
            self.frames.append(data)
        stream.stop_stream()
        stream.close()
        p.terminate()

    def stop(self):
        self.continue_flag = False

    def save(self):     # 自动命令
        self.filename = time.strftime("%Y%m%d%H%M%S")
        self.save_to_file(self.filename)

    def save_to_file(self, filename: str):  # 可手动命令
        if not filename.endswith(".wav"):
            filename += ".wav"
        p = pyaudio.PyAudio()
        wav_file = wave.open(filename, 'wb')
        wav_file.setnchannels(self.channels)
        wav_file.setsampwidth(p.get_sample_size(self.format))
        wav_file.setframerate(self.rate)
        wav_file.writeframes(b''.join(self.frames))
        wav_file.close()
        print("录音已保存为{}!".format(filename))


def play_wav(_filename, chunk=1024):
    if not _filename.endswith(".wav"):
        _filename += ".wav"
    wav_file = wave.open(_filename, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wav_file.getsampwidth()),
                    channels=wav_file.getnchannels(),
                    rate=wav_file.getframerate(),
                    output=True)
    frames = wav_file.readframes(chunk)
    while frames != b'':
        stream.write(frames)
        frames = wav_file.readframes(chunk)
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("播放结束")


if __name__ == '__main__':
    record = Recorder()
    record.start()

    time1 = time.time()
    b = input("录音中......按Enter停止")

    record.stop()
    time2 = time.time()
    print("录音时长：{}秒".format(round(time2-time1, 1)))
    record.save()
    play_wav(record.filename)


