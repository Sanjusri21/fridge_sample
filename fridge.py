#import speech_recognition as sr
#import pyttsx3
#
## -------------------- FOOD DATABASE --------------------
#food_data = {
#    "milk": 2,
#    "eggs": 7,
#    "chicken": 1,
#    "cheese": 5,
#    "apple": 4
#}
#
## -------------------- USER POINTS --------------------
#points = 100
#
## -------------------- SPEAK --------------------
#def speak(text):
#    print("AI:", text)
#    engine = pyttsx3.init()
#    engine.setProperty("rate", 150)
#    engine.setProperty("volume", 1)
#    engine.say(text)
#    engine.runAndWait()
#    engine.stop()
#
## -------------------- LISTEN --------------------
#def listen():
#    r = sr.Recognizer()
#    r.energy_threshold = 300
#    r.dynamic_energy_threshold = True
#    r.pause_threshold = 0.8
#
#    with sr.Microphone() as source:
#        print("\n🎤 Listening...")
#        r.adjust_for_ambient_noise(source, duration=1)
#        audio = r.listen(source, timeout=5, phrase_time_limit=10)
#
#    try:
#        text = r.recognize_google(audio)
#        print("You:", text)
#        return text.lower()
#    except:
#        return ""
#
## -------------------- PUNISHMENT CHECK --------------------
#def check_punishment():
#    global points
#
#    if points <= 10:
#        speak("Critical warning. Executing punishment now.")
#        speak("Turning off the fridge. Please clean it immediately.")
#        print("❌ FRIDGE POWER OFF (SIMULATED)")
#        return True
#
#    elif points <= 30:
#        speak("Warning. If we don't cook this food, I will turn off the fridge.")
#        speak("You should only clean it.")
#    
#    return False
#
## -------------------- PROCESS QUERY --------------------
#def process_query(query):
#    global points
#    responses = []
#
#    for item, days in food_data.items():
#        if item in query:
#            points += 5  # reward for checking food
#
#            if days == 1:
#                responses.append(f"{item.capitalize()} expires in 1 day.")
#            else:
#                responses.append(f"{item.capitalize()} expires in {days} days.")
#
#    if responses:
#        responses.append(f"Your current points are {points}.")
#        return " ".join(responses)
#
#    # If user says random / ignores food
#    points -= 10
#    check_punishment()
#    return f"I do not have information about that item. Points reduced to {points}."
#
## -------------------- MAIN LOOP --------------------
#def main():
#    global points
#    speak("Hello. I am Alina the Smart Fridge. Please ask about your food items.")
#
#    while True:
#        query = listen()
#
#        if not query:
#            continue
#
#        if "exit" in query or "quit" in query:
#            speak("Goodbye. Have a fresh day.")
#            break
#
#        response = process_query(query)
#        speak(response)
#
#        if check_punishment():
#            break
#
## -------------------- RUN --------------------
#if __name__ == "__main__":
#    main()
#import speech_recognition as sr
#import pyttsx3
#import time
#
## -------------------- FOOD DATABASE --------------------
#food_data = {
#    "milk": 2,
#    "eggs": 7,
#    "chicken": 1,
#    "cheese": 5,
#    "apple": 4
#}
#
## -------------------- USER POINTS --------------------
#points = 100
#
## -------------------- VOICE ENGINE (FORCED WINDOWS VOICE) --------------------
#engine = pyttsx3.init(driverName="sapi5")
#
#voices = engine.getProperty("voices")
#engine.setProperty("voice", voices[0].id)   # 🔴 FORCE VOICE
#
#engine.setProperty("rate", 150)
#engine.setProperty("volume", 1.0)
#
#def speak(text):
#    print("AI:", text)
#    engine.say(text)
#    engine.runAndWait()
#    time.sleep(0.4)   # 🔴 audio release delay
#
## -------------------- SPEECH RECOGNITION --------------------
#recognizer = sr.Recognizer()
#recognizer.energy_threshold = 200
#recognizer.dynamic_energy_threshold = True
#recognizer.pause_threshold = 0.8
#
#def listen():
#    with sr.Microphone() as source:
#        print("🎤 Listening...")
#        recognizer.adjust_for_ambient_noise(source, duration=0.5)
#        try:
#            audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
#        except sr.WaitTimeoutError:
#            return ""
#
#    try:
#        text = recognizer.recognize_google(audio).lower()
#        print("You:", text)
#        time.sleep(0.5)   # 🔴 mic release delay
#        return text
#    except:
#        return ""
#
## -------------------- PUNISHMENT SYSTEM --------------------
#def check_punishment():
#    global points
#
#    if points <= 10:
#        speak("Critical level reached.")
#        speak("Turning off the fridge. Please clean it immediately.")
#        print("❌ FRIDGE POWER OFF (SIMULATED)")
#        return True
#
#    elif points <= 30:
#        speak("Warning. Food is being wasted.")
#        speak("If you ignore again, I will turn off the fridge.")
#
#    return False
#
## -------------------- LIST ALL PRODUCTS --------------------
#def list_all_products():
#    global points
#
#    least_item = None
#    least_days = 999
#
#    speak("Here are the products inside the fridge.")
#
#    for item, days in food_data.items():
#        speak(f"{item.capitalize()} has {days} days left")
#
#        if days < least_days:
#            least_days = days
#            least_item = item
#
#    speak(
#        f"{least_item.capitalize()} is going to expire soon. "
#        f"You should cook food using {least_item} today."
#    )
#
#    points += 5
#    speak(f"Your current points are {points}.")
#
## -------------------- PROCESS QUERY --------------------
#def process_query(query):
#    global points
#
#    if (
#        "what are the products" in query
#        or "what do we have" in query
#        or "list all items" in query
#        or "what is inside" in query
#        or "what can i cook today" in query
#    ):
#        list_all_products()
#        return
#
#    for item, days in food_data.items():
#        if item in query:
#            points += 5
#            speak(f"{item.capitalize()} has {days} days left.")
#            speak(f"Your current points are {points}.")
#            return
#
#    points -= 10
#    speak("I do not have information about that.")
#    speak(f"Points reduced to {points}.")
#    check_punishment()
#
## -------------------- MAIN LOOP --------------------
#def main():
#    speak("Hello. I am Alina, the Smart Fridge.")
#
#    while True:
#        query = listen()
#
#        if not query:
#            continue
#
#        if "exit" in query or "quit" in query:
#            speak("Goodbye. Have a fresh day.")
#            break
#
#        process_query(query)
#
#        if check_punishment():
#            break
#
## -------------------- RUN --------------------
#if __name__ == "__main__":
#    main()
#import speech_recognition as sr
#import win32com.client
#import time
#
## -------------------- WINDOWS VOICE (100% STABLE) --------------------
#speaker = win32com.client.Dispatch("SAPI.SpVoice")
#speaker.Rate = 0
#speaker.Volume = 100
#
#def speak(text):
#    print("AI:", text)
#    speaker.Speak(text)
#    speaker.runAndWait()
#    time.sleep(0.2)
#
## -------------------- FOOD DATABASE --------------------
#food_data = {
#    "milk": 2,
#    "eggs": 7,
#    "chicken": 1,
#    "cheese": 5,
#    "apple": 4
#}
#
## -------------------- USER POINTS --------------------
#points = 100
#
## -------------------- SPEECH RECOGNITION --------------------
#recognizer = sr.Recognizer()
#recognizer.energy_threshold = 250
#recognizer.dynamic_energy_threshold = True
#recognizer.pause_threshold = 0.8
#
#def listen():
#    with sr.Microphone() as source:
#        print("🎤 Listening...")
#        recognizer.adjust_for_ambient_noise(source, duration=0.6)
#        try:
#            audio = recognizer.listen(source, timeout=5, phrase_time_limit=6)
#        except sr.WaitTimeoutError:
#            return ""
#
#    try:
#        text = recognizer.recognize_google(audio).lower()
#        print("You:", text)
#        time.sleep(0.2)
#        return text
#    except:
#        return ""
#
## -------------------- PUNISHMENT SYSTEM --------------------
#def check_punishment():
#    global points
#
#    if points <= 10:
#        speak("Critical level reached.")
#        speak("Turning off the fridge. Please clean it immediately.")
#        print("❌ FRIDGE POWER OFF (SIMULATED)")
#        return True
#
#    elif points <= 30:
#        speak("Warning. Food is being wasted.")
#        speak("If you ignore again, I will turn off the fridge.")
#
#    return False
#
## -------------------- LIST ALL PRODUCTS --------------------
#def list_all_products():
#    global points
#
#    least_item = None
#    least_days = 999
#
#    speak("Here are the products inside the fridge.")
#
#    for item, days in food_data.items():
#        speak(f"{item.capitalize()} expires in {days} days.")
#
#        if days < least_days:
#            least_days = days
#            least_item = item
#
#    speak(
#        f"{least_item.capitalize()} is going to expire soon. "
#        f"You should cook food using {least_item} today."
#    )
#
#    points += 5
#    speak(f"Your current points are {points}.")
#
## -------------------- PROCESS QUERY --------------------
#def process_query(query):
#    global points
#
#    if (
#        "what are the products" in query
#        or "what do we have" in query
#        or "list all items" in query
#        or "what is inside" in query
#        or "what can i cook today" in query
#    ):
#        list_all_products()
#        return
#
#    for item, days in food_data.items():
#        if item in query:
#            points += 5
#            speak(
#                f"{item.capitalize()} expires in {days} day."
#                if days == 1
#                else f"{item.capitalize()} expires in {days} days."
#            )
#            speak(f"Your current points are {points}.")
#            return
#
#    points -= 10
#    speak("I do not have information about that.")
#    speak(f"Points reduced to {points}.")
#    check_punishment()
#
## -------------------- MAIN LOOP --------------------
#def main():
#    speak("Hello. I am Alina, the Smart Fridge.")
#
#    while True:
#        query = listen()
#
#        if not query:
#            continue
#
#        if "exit" in query or "quit" in query:
#            speak("Goodbye. Have a fresh day.")
#            break
#
#        process_query(query)
#
#        if check_punishment():
#            break
#
## -------------------- RUN --------------------
#if __name__ == "__main__":
#    main()
import speech_recognition as sr
import subprocess
import time

# -------------------- FOOD DATABASE --------------------
food_data = {
    "milk": 2,
    "eggs": 7,
    "chicken": 1,
    "cheese": 5,
    "apple": 4
}

points = 100

# -------------------- WINDOWS VOICE (NO pyttsx3) --------------------
def speak(text):
    print("AI:", text)
    safe_text = text.replace("'", "")
    command = f'''
    Add-Type -AssemblyName System.Speech;
    $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer;
    $speak.Speak('{safe_text}');
    '''
    subprocess.run(
        ["powershell", "-Command", command],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(0.1)

# -------------------- SPEECH RECOGNITION --------------------
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.7

mic = sr.Microphone()

with mic as source:
    print("🔧 Calibrating microphone...")
    recognizer.adjust_for_ambient_noise(source, duration=1)

def listen():
    with mic as source:
        print("🎤 Listening...")
        try:
            audio = recognizer.listen(
                source,
                timeout=4,
                phrase_time_limit=5
            )
        except sr.WaitTimeoutError:
            return ""

    try:
        text = recognizer.recognize_google(audio).lower()
        print("You:", text)
        return text
    except:
        return ""

# -------------------- LOGIC --------------------
def list_all_products():
    global points

    least_item = min(food_data, key=food_data.get)

    speak("Here are the items in the fridge.")
    for item, days in food_data.items():
        speak(f"{item} expires in {days} days.")

    speak(f"{least_item} will expire soon.")
    points += 5
    speak(f"Your points are {points}.")

def process_query(query):
    global points

    if any(x in query for x in ["list", "products", "inside", "cook"]):
        list_all_products()
        return

    for item, days in food_data.items():
        if item in query:
            speak(f"{item} expires in {days} days.")
            points += 5
            speak(f"Your points are {points}.")
            return

    points -= 10
    speak("I do not recognize that item.")
    speak(f"Points reduced to {points}.")

# -------------------- MAIN LOOP --------------------
def main():
    speak("Hello. I am Alina, the smart fridge.")

    while True:
        query = listen()

        if not query:
            continue

        if "exit" in query or "quit" in query:
            speak("Goodbye. Have a fresh day.")
            break

        process_query(query)

# -------------------- RUN --------------------
if __name__ == "__main__":
    main()
