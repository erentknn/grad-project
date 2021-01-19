import RPi.GPIO as GPIO
import os
import sys
import logging
import subprocess
import threading
import time


# KULLANICI DEĞİŞKENLERİ
DEBUG = 0  # Debug 0/1 Kapalı/Açık (Debug.log’a kullanımları yazar.)
SPEED = 1.0  # Konuşma Hızı 0.5- 2.0
VOLUME = 90  # Ses Seviyesi
# DİĞER AYARLAR
SOUNDS = "/home/pi/PiTextReader/sounds/"  # Ses dosyalarının kaydedildiği kısım
CAMERA = "raspistill -cfx 128:128 --awb auto -rot 180 -t 500 -o /tmp/image.jpg"

# GPIO BUTONLARI
BTN1 = 24  # Buton
LED = 18  # LED

# FONKSİYONLAR
# Arka plandaki işlemler için kontroller


class RaspberryThread(threading.Thread):
    def __init__(self, function):
        self.running = False
        self.function = function
        super(RaspberryThread, self).__init__()

    def start(self):
        self.running = True
        super(RaspberryThread, self).start()

    def run(self):
        while self.running:
            self.function()

    def stop(self):
        self.running = False

# LED AÇIK/KAPALI


def led(val):
    logger.info('led('+str(val)+')')
    if val:
        GPIO.output(LED, GPIO.HIGH)
    else:
        GPIO.output(LED, GPIO.LOW)

# SESİ OYNAT


def sound(val):
    logger.info('sound()')
    time.sleep(0.2)
    cmd = "/usr/bin/aplay -q "+str(val)
    logger.info(cmd)
    os.system(cmd)
    return

# KONUŞMA DURUMU


def speak(val):  # TTS
    logger.info('speak()')
    cmd = "/usr/bin/flite -voice awb --setf duration_stretch=" + \
        str(SPEED)+" -t \""+str(val)+"\""
    logger.info(cmd)
    os.system(cmd)
    return

# SES AYARLAMA


def volume(val):  # Başlangıç için sesi ayarlama
    logger.info('volume('+str(val)+')')
    vol = int(val)
    cmd = "sudo amixer -q sset PCM,0 "+str(vol)+"%"
    logger.info(cmd)
    os.system(cmd)
    return

# TEXT TEMİZLEME


def cleanText():
    logger.info('cleanText()')
    cmd = "sed -e 's/\([0-9]\)/& /g' -e 's/[[:punct:]]/ /g' -e 'G' -i /tmp/text.txt"
    logger.info(cmd)
    os.system(cmd)
    return

# TTS’İ BAŞLAT


def playTTS():
    logger.info('playTTS()')
    global current_tts
    current_tts = subprocess.Popen(['/usr/bin/flite', '-voice', 'awb', '-f', '/tmp/text.txt'],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, close_fds=True)
    rt.start()
    current_tts.communicate()
    return

# TTS’İ DURDUR


def stopTTS():
    global current_tts
    if GPIO.input(BTN1) == GPIO.LOW:
        logger.info('stopTTS()')
        # current_tts.terminate()
        current_tts.kill()
        time.sleep(0.5)
    return

# RESMİ ÇEKME VE YAZIYI ALMA


def getData():
    logger.info('getData()')
    led(0)  # Turn off Button LED
    sound(SOUNDS+"camera-shutter.wav")
    cmd = CAMERA
    logger.info(cmd)
    os.system(cmd)
    speak("now working. please wait.")
    cmd = "/usr/bin/tesseract /tmp/image.jpg /tmp/text"
    logger.info(cmd)
    os.system(cmd)

    cleanText()
    playTTS()
    return


# ANA FONKSİYON
try:
    global rt
    # Setup Logging
    logger = logging.getLogger()
    handler = logging.FileHandler('debug.log')
    if DEBUG:
        logger.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)
        handler.setLevel(logging.ERROR)
    log_format = '%(asctime)-6s: %(name)s - %(levelname)s - %(message)s'
    handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(handler)
    logger.info('Starting')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BTN1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LED, GPIO.OUT)
    rt = RaspberryThread(function=stopTTS)
    volume(VOLUME)
    speak("OK, ready")
    led(1)
    while True:
        if GPIO.input(BTN1) == GPIO.LOW:
            # Btn 1
            getData()
            rt.stop()
            rt = RaspberryThread(function=stopTTS)
            led(1)
            time.sleep(0.5)
            speak("OK, ready")
            time.sleep(0.2)
except KeyboardInterrupt:
    logger.info("exiting")
GPIO.cleanup()
sys.exit(0)
