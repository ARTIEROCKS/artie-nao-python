from service import queue_service
from threading import Thread
import speech_recognition as sr

if __name__ == "__main__":

    # We get the environment
    t = Thread(target=queue_service.start_consuming)
    t.start()
    #r = sr.Recognizer()
    #with sr.Microphone() as source:
    #    r.adjust_for_ambient_noise(source)
    #    print("Please, say something")
    #    audio = r.listen(source)
    #    print("Recognizing Now... ")

    #    try:
    #        dest = r.recognize_google(audio, language="es-ES ")
    #        print("You have said: " + dest)
    #    except Exception as e:
    #        print("Error :" + str(e))