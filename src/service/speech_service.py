import speech_recognition as sr
import beepy as beep
import os
import whisper
import tempfile
import numpy as np

class SpeechService:

    def __init__(self, language="spanish", whisper_model="medium"):
        self.language = language
        self.r = sr.Recognizer()
        # Configuración optimizada para español
        self.r.energy_threshold = 200  # Más sensible (default es 300)
        self.r.dynamic_energy_threshold = True
        self.r.pause_threshold = 0.8  # Reducir tiempo de pausa
        self.r.phrase_threshold = 0.3
        self.r.non_speaking_duration = 0.5

        # Cargar modelo de Whisper
        # Opciones: tiny, base, small, medium, large
        # base es un buen balance entre velocidad y precisión
        print(f"[INFO] Cargando modelo Whisper '{whisper_model}'...")
        self.whisper_model = whisper.load_model(whisper_model)
        print("[INFO] Modelo Whisper cargado exitosamente")

    def listen(self):
        dest = None

        try:
            with sr.Microphone() as source:
                # Ajustar para ruido ambiente
                print("Ajustando para ruido ambiente... Por favor espera.")
                self.r.adjust_for_ambient_noise(source, duration=1)

                print(f"[DEBUG] Umbral de energía después del ajuste: {self.r.energy_threshold}")
                print(f"[DEBUG] Configuración del micrófono lista")
                print("Por favor, di algo...")
                beep.beep('coin')

                # Escuchar con timeout
                audio = self.r.listen(source, timeout=15, phrase_time_limit=7)

                print("[DEBUG] Audio capturado exitosamente")
                print("Reconociendo ahora con Whisper... ")
                beep.beep('ping')

                # Guardar audio temporalmente para Whisper
                audio_data = audio.get_wav_data()

                # Guardar también para debugging
                try:
                    with open("last_audio.wav", "wb") as f:
                        f.write(audio_data)
                    print("[DEBUG] Audio guardado en 'last_audio.wav' para análisis")
                except:
                    pass

                # Crear archivo temporal para Whisper
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                    tmp_file.write(audio_data)
                    tmp_filename = tmp_file.name

                try:
                    # Transcribir con Whisper
                    # language="es" fuerza el español, mejorando la precisión
                    result = self.whisper_model.transcribe(
                        tmp_filename,
                        language="es",
                        fp16=False  # Desactivar fp16 para compatibilidad
                    )

                    dest = result["text"].strip()

                    if dest:
                        # Limpiar el texto
                        dest = dest.replace(',', '').replace('"', '').replace('*','')
                        print(f"Has dicho: {dest}")
                        print(f"[DEBUG] Confianza del modelo: Se detectó texto correctamente")
                    else:
                        print("[ERROR] Whisper no detectó ningún texto en el audio")
                        dest = None

                except Exception as whisper_error:
                    print(f"[ERROR] Error al procesar con Whisper: {whisper_error}")
                    dest = None
                finally:
                    # Limpiar archivo temporal
                    try:
                        os.unlink(tmp_filename)
                    except:
                        pass

        except sr.WaitTimeoutError:
            print("[ERROR] No se detectó ningún sonido en el tiempo límite")
            print("[SUGERENCIA] Verifica que el micrófono correcto esté seleccionado")
            dest = None
        except Exception as e:
            print(f"[ERROR] Error inesperado: {str(e)}")
            import traceback
            traceback.print_exc()
            dest = None

        return dest