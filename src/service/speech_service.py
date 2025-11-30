import speech_recognition as sr
from whisper_mic import WhisperMic
import beepy as beep

class SpeechService:

    def __init__(self, language="es-ES"):
        self.language = language
        self.r = sr.Recognizer()

    def listen(self):
        dest = None

        try:
            mic = WhisperMic()
            if not mic.mic_active:
                mic.toggle_microphone()

            print("Please, say something")
            beep.beep('coin')

            dest = mic.listen(timeout=3, phrase_time_limit=3)

            print("Recognizing Now... ")
            beep.beep('ping')

            dest = dest.replace(',', '').replace('"', '').replace('*','')
            print("You have said: " + dest)

        except Exception as e:
            print("Error :" + str(e))

        #with sr.Microphone() as source:
            #self.r.adjust_for_ambient_noise(source)
            #print("Please, say something")
            #beep.beep('coin')

            #audio = self.r.listen(source, timeout=10)
            #print("Recognizing Now... ")
            #beep.beep('ping')

            #try:
               # dest = self.r.recognize_google(audio, language=self.language)
                #dest = dest.replace(',', '').replace('"', '')
                #print("You have said: " + dest)
            #except Exception as e:
                #print("Error :" + str(e))

        return dest