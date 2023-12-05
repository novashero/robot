import threading
import numpy as np
import face_recognition
import cv2
import os
import json
from datetime import datetime
import pymysql
from config import host, user, password, db_name
import pymysql
from config import host, user, password, db_name
import RPi.GPIO as GPIO
import time
from time import sleep
from rpi_ws281x import Adafruit_NeoPixel
from rpi_ws281x import Color
import pyaudio
from vosk import Model, KaldiRecognizer
model = Model("vosk-model-small-ru-0.22")
path = 'KnownFaces'
images = []
classNames = []
myList = os.listdir(path)
print(myList)


rec = KaldiRecognizer(model, 16000)
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
GPIO.output(18, GPIO.HIGH)


LED_COUNT      = 112      
LED_PIN        = 10     
LED_FREQ_HZ    = 800000  
LED_DMA        = 10     
LED_BRIGHTNESS = 0     
LED_INVERT     = False   
LED_CHANNEL    = 0       

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT)

strip.begin()


servoPIN = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(servoPIN, GPIO.OUT)
GPIO.setup(23, GPIO.OUT)
p = GPIO.PWM(servoPIN, 32) 
p.start(8) 
p.ChangeDutyCycle(5)

GPIO.output(23, True)
#GPIO.output(18, False)
fff = 0



def colorWipe(strip, color, wait_ms=50):
    """Заполнение ленты цветом по одному светодиоду."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)
colorWipe(strip, Color(88, 0, 0), wait_ms=5)
for cls in myList:
    curImg = cv2.imread(f'{path}/{cls}')
    images.append(curImg)
    classNames.append(os.path.splitext(cls)[0])
print(classNames)

connection = pymysql.connect(
    host=host,
    port=3306,
    user=user,
    password=password,
    database=db_name,
    cursorclass=pymysql.cursors.DictCursor
    )
print("successfully connected...")
print("#" * 20)
def colorred():
    colorWipe(strip, Color(255, 0, 0), wait_ms=5)
    

def waiter():
    colorWipe(strip, Color(0, 255, 255), wait_ms=5)


def colorgreen():
    colorWipe(strip, Color(0, 255, 0), wait_ms=5)
    

def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

now = datetime.now()
time2 = now.strftime("%H:%M:%S")
na2me = 'ivan'
temp = '36.6'
time2 = '22:12'
temp2 = '36.24'




def markAttendance(name):
    with open("Attendance.csv", "r+") as f:
        myDataList = f.readlines()
        nameList = []
        for line in myDataList:
            entry = line.split(',')
            nameList.append(entry[0])
            with connection.cursor() as cursor:
                now = datetime.now()
                time2 = now.strftime("%H:%M:%S")
                update_time = "UPDATE `info` SET time = ('%(time)s') WHERE name = ('%(name)s')" % ({'time': time2, 'name': name, 'temp': temp2})
                update_timper = "UPDATE `info` SET temp = ('%(temp)s') WHERE name = ('%(name)s')" % ({'time': time2, 'name': name, 'temp': temp2})
                cursor.execute(update_time)
                cursor.execute(update_timper)


                connection.commit()
        if name not in nameList:
            now = datetime.now()
            dtString = now.strftime("%H:%M:%S")
            time2 = now.strftime("%H:%M:%S")
            f.writelines(f'\n{name}, {dtString}')
            with connection.cursor() as cursor:
                insert_query = "INSERT INTO `info` (name, time, temp) VALUES ('%(name)s', '%(time)s', '%(temp)s')" % ({'time': time2, 'name': name, 'temp': temp})
                cursor.execute(insert_query)
                connection.commit()
            print(name)
        



encodeListKnown = findEncodings(images)
print("Декодирование закончено")
GPIO.output(23, False)
cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    facesCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)
    data = stream.read(4000, exception_on_overflow=False)
    def listen():
        if rec.AcceptWaveform(data) and len(data) > 0:
            answer = json.loads(rec.Result())
            if answer["text"]:
                yield answer["text"]
                
 
    fff += 1
    print(fff)
    if fff == 50:
        colorred()
    if fff == 1:
        colorgreen()
    if fff == 200:
        waiter()
    
    for encodeFace, faceLoc in zip(encodeCurFrame, facesCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        print(faceDis)

        
        matchIndex = np.argmin(faceDis)
        if matches[matchIndex]:
            name = classNames[matchIndex]
            print(name)
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
            cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
            markAttendance(name)
            fff = 0
    for text in listen():
        print(text)
        #if text == "раз":

    #colorWipe(strip, Color(255, 0, 0), wait_ms=5)  # Заполнение красным
     #   if text == "привет":
      #      print('привет')

        if text == "обзор":
            #colorWipe(strip, Color(255, 105, 180), wait_ms=100)  #
            GPIO.output(18, GPIO.LOW)
            time.sleep(0.5)                 # wait half a second
            GPIO.output(18, GPIO.HIGH)
        if text == "стоп":
            colorWipe(strip, Color(0, 0, 0), wait_ms=50)
            print("ну и хорошо")
        if text == "синий":
            print("синий")
            colorWipe(strip, Color(0, 0, 255), wait_ms=5)  # 
        if text == "зелёный":
            colorWipe(strip, Color(0, 255, 0), wait_ms=5)  # 
            print("зелёный")       
    cv2.imshow("WebCam", img)
    cv2.waitKey(1)
    

