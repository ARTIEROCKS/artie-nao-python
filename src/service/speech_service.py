import speech_recognition as sr

class SpeechService:

    def __init__(self, language="es-ES"):
        self.language = language
        self.r = sr.Recognizer()

    def listen(self):

        dest = None
        with sr.Microphone() as source:
            self.r.adjust_for_ambient_noise(source)
            print("Please, say something")
            audio = self.r.listen(source)
            print("Recognizing Now... ")

            try:
                dest = self.r.recognize_google(audio, language=self.language)
                print("You have said: " + dest)
            except Exception as e:
                print("Error :" + str(e))

        return dest