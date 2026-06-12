import pyttsx3
import time

engine = pyttsx3.init(driverName='sapi5')
engine.setProperty('rate', 150)

engine.say("Alina voice test successful")
engine.runAndWait()

time.sleep(2)
