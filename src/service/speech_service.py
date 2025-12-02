import speech_recognition as sr
import beepy as beep
import os
import whisper
import tempfile
from pathlib import Path
from datetime import datetime
import re

class SpeechService:

    def __init__(self, language="spanish", whisper_model="medium"):
        self.language = language
        self.r = sr.Recognizer()
        # Optimized configuration for Spanish speech
        self.r.energy_threshold = 200  # Lower threshold captures softer voices
        self.r.dynamic_energy_threshold = True
        self.r.pause_threshold = 0.8  # Shorter pause window
        self.r.phrase_threshold = 0.3
        self.r.non_speaking_duration = 0.5

        self.project_root = Path(__file__).resolve().parents[2]
        self.records_dir = self.project_root / "recordings"
        self.records_dir.mkdir(parents=True, exist_ok=True)
        self.last_audio_path = self.records_dir / "last_audio.wav"

        # Load Whisper model: tiny, base, small, medium, large (base balances speed/accuracy)
        print(f"[INFO] Loading Whisper model '{whisper_model}'...")
        self.whisper_model = whisper.load_model(whisper_model)
        print("[INFO] Whisper model loaded successfully")

    def listen(self, child_name=None):
        dest = None
        tmp_filename = None
        audio_saved = False

        try:
            with sr.Microphone() as source:
                # Calibrate to ambient noise
                print("Calibrating for ambient noise... please wait.")
                self.r.adjust_for_ambient_noise(source, duration=1)

                print(f"[DEBUG] Energy threshold after calibration: {self.r.energy_threshold}")
                print(f"[DEBUG] Microphone configuration ready")
                print("Please, say something...")
                beep.beep('coin')

                # Listen with timeout
                audio = self.r.listen(source, timeout=15, phrase_time_limit=10)

                print("[DEBUG] Audio captured successfully")
                print("Transcribing with Whisper now... ")
                beep.beep('ping')

                # Encode audio for Whisper
                audio_data = audio.get_wav_data()

                # Persist raw capture for debugging
                audio_saved = self._persist_last_audio(audio_data)

                # Temporary file for Whisper interaction
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                    tmp_file.write(audio_data)
                    tmp_filename = tmp_file.name

                try:
                    # Force Spanish for higher accuracy
                    result = self.whisper_model.transcribe(
                        tmp_filename,
                        language="es",
                        fp16=False  # Disable fp16 for compatibility
                    )

                    dest = result["text"].strip()

                    if dest:
                        # Basic cleanup
                        dest = dest.replace(',', '').replace('"', '').replace('*','')
                        print(f"You said: {dest}")
                        print(f"[DEBUG] Model confidence: text detected correctly")
                    else:
                        print("[ERROR] Whisper did not detect any text in the audio")
                        dest = None

                except Exception as whisper_error:
                    print(f"[ERROR] Whisper processing error: {whisper_error}")
                    dest = None
                finally:
                    if tmp_filename and os.path.exists(tmp_filename):
                        try:
                            os.unlink(tmp_filename)
                        except:
                            pass

        except sr.WaitTimeoutError:
            print("[ERROR] No sound detected within the time limit")
            print("[TIP] Ensure the correct microphone is selected")
            dest = None
        except Exception as e:
            print(f"[ERROR] Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            dest = None

        if audio_saved:
            self._archive_last_audio(child_name)

        return dest

    def _persist_last_audio(self, audio_data):
        try:
            self.last_audio_path.write_bytes(audio_data)
            print(f"[DEBUG] Audio saved to '{self.last_audio_path}' for analysis")
            return True
        except Exception as exc:
            print(f"[WARN] Failed to store the recording: {exc}")
            return False

    def _archive_last_audio(self, child_name):
        if not self.last_audio_path.exists():
            return

        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        sanitized_child = self._sanitize_child_name(child_name)
        target = self.records_dir / f"{timestamp}_{sanitized_child}_audio.wav"

        counter = 1
        while target.exists():
            target = self.records_dir / f"{timestamp}_{sanitized_child}_audio_{counter}.wav"
            counter += 1

        try:
            self.last_audio_path.rename(target)
            print(f"[DEBUG] Audio archived as '{target.name}'")
        except Exception as exc:
            print(f"[WARN] Failed to archive the recording: {exc}")

    def _sanitize_child_name(self, child_name):
        cleaned = re.sub(r"[^A-Za-z0-9]+", "_", child_name or "UNKNOWN").strip('_')
        return cleaned or "UNKNOWN"
