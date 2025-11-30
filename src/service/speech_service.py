import speech_recognition as sr
from whisper_mic import WhisperMic
import beepy as beep
import os

class SpeechService:

    def __init__(self, language="es-ES"):
        self.language = language
        self.r = sr.Recognizer()
        # Configuración optimizada para español
        self.r.energy_threshold = 200  # Más sensible (default es 300)
        self.r.dynamic_energy_threshold = True
        self.r.pause_threshold = 0.8  # Reducir tiempo de pausa
        self.r.phrase_threshold = 0.3
        self.r.non_speaking_duration = 0.5

    def listen(self):
        dest = None

        try:
            with sr.Microphone() as source:
                # Ajustar para ruido ambiente
                print("Ajustando para ruido ambiente... Por favor espera.")
                self.r.adjust_for_ambient_noise(source, duration=1)

                print(f"[DEBUG] Umbral de energía después del ajuste: {self.r.energy_threshold}")
                print(f"[DEBUG] Configuración del micrófono lista")
                print("Por favor, di algo... (habla ALTO y CLARO)")
                beep.beep('coin')

                # Escuchar con timeout más largo
                audio = self.r.listen(source, timeout=15, phrase_time_limit=7)

                print("[DEBUG] Audio capturado exitosamente")
                print("Reconociendo ahora... ")
                beep.beep('ping')

                # Guardar audio para debugging (opcional)
                try:
                    with open("last_audio.wav", "wb") as f:
                        f.write(audio.get_wav_data())
                    print("[DEBUG] Audio guardado en 'last_audio.wav' para análisis")
                except:
                    pass

                # Intentar reconocimiento con Google
                try:
                    dest = self.r.recognize_google(audio, language=self.language)
                    dest = dest.replace(',', '').replace('"', '').replace('*','')
                    print("Has dicho: " + dest)
                except sr.UnknownValueError:
                    print("[ERROR] Google no pudo entender el audio.")
                    print("[DEBUG] Intentando con configuración alternativa...")

                    # Segundo intento con el audio capturado
                    try:
                        dest = self.r.recognize_google(audio, language="es-ES", show_all=False)
                        if dest:
                            dest = dest.replace(',', '').replace('"', '').replace('*','')
                            print("Has dicho (segundo intento): " + dest)
                        else:
                            raise sr.UnknownValueError()
                    except:
                        print("[ERROR] Tampoco funcionó el segundo intento.")
                        print("[SUGERENCIA] Verifica:")
                        print("  - Que el micrófono esté funcionando correctamente")
                        print("  - Que tengas conexión a internet")
                        print("  - Habla más alto y claro")
                        print("  - Revisa el archivo 'last_audio.wav' para ver si grabó algo")
                        dest = None

        except sr.WaitTimeoutError:
            print("[ERROR] No se detectó ningún sonido en el tiempo límite")
            print("[SUGERENCIA] Verifica que el micrófono correcto esté seleccionado")
            dest = None
        except sr.RequestError as e:
            print(f"[ERROR] Error con el servicio de reconocimiento de voz: {e}")
            print("[SUGERENCIA] Verifica tu conexión a internet")
            dest = None
        except Exception as e:
            print(f"[ERROR] Error inesperado: {str(e)}")
            import traceback
            traceback.print_exc()
            dest = None

            #try:
               # dest = self.r.recognize_google(audio, language=self.language)
                #dest = dest.replace(',', '').replace('"', '')
                #print("You have said: " + dest)
            #except Exception as e:
                #print("Error :" + str(e))

        return dest