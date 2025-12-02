import qi
import pika
import time
import datetime
import json
from service.speech_service import SpeechService
from motion import bored, happy, kisses, thinking, fear, excited, chill, curious, confused

class NAOService:

    @staticmethod
    def normalize_text_for_nao(text):
        """
        Normaliza el texto reemplazando caracteres Unicode problemáticos
        por sus equivalentes ASCII que el robot NAO puede procesar.
        """
        if not text:
            return text

        # Reemplazar comillas tipográficas por comillas normales
        text = text.replace('\u201c', '"').replace('\u201d', '"')  # " "
        text = text.replace('\u2018', "'").replace('\u2019', "'")  # ' '
        text = text.replace('\u201a', ',').replace('\u201b', "'")

        # Reemplazar guiones especiales
        text = text.replace('\u2013', '-').replace('\u2014', '-')  # – —

        # Reemplazar puntos suspensivos
        text = text.replace('\u2026', '...')  # …

        return text

    tone_mapping = {
        "HIGH": 1.25,
        "MEDIUMHIGH": 1.10,
        "MEDIUM": 1.0,
        "MEDIUMLOW": 0.9,
        "LOW": 0.8
    }
    speed_mapping = {
        "HIGH": 90,
        "MEDIUMHIGH": 85,
        "MEDIUM": 80,
        "MEDIUMLOW": 75,
        "LOW": 70
    }
    leds_mapping = {
        "HAPPY": 0x0000FF00,  # Green
        "ANGRY": 0x00FFFF00,  # Yellow
        "CONTEMPT": 0x000000FF,  # Blue
        "CALM": 0x00FFFFFF,  # White
        "VERYANGRY": 0x00FF0000,  # Red
        "ENCOURAGE": 0x00FF00FF,  # Magenta
        "NEUTRAL": 0x0000FFFF  # Cyan
    }

    vocabulary = ["si", "no"]

    def __init__(self, queue_channel=None, conversation_queue=None, robot_address=None):
        self.asr = None
        self.memory = None
        self.context_id = None
        self.user_id = None
        self.channel = queue_channel
        self.conversation_queue = conversation_queue
        self.last_bmle_execution_time = None  # Stores the last execution timestamp

        # Attempt to connect with retry mechanism
        self.session = self.connect_with_retry(robot_address=robot_address)

        # Once done, we wake up NAO and go to stand posture
        motion = self.session.service("ALMotion")
        motion.wakeUp()

        posture = self.session.service("ALRobotPosture")
        posture.goToPosture("StandInit", 0.5)


        # Initializes Speech Service
        self.speech_service = SpeechService()

    def connect_with_retry(self, max_retries=5, delay=5, robot_address = None):
        """Attempts to connect to the NAO robot, retrying in case of failure."""
        for attempt in range(max_retries):
            try:
                session = qi.Session()
                session.connect(robot_address)
                print(f"Successfully connected to NAO: {robot_address}")
                return session
            except Exception as e:
                print(f"[ERROR] Connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay)  # Wait before retrying
                else:
                    raise Exception("Failed to connect to NAO after multiple attempts.")

    def get_last_execution_time_difference(self):

        """Returns the last execution timestamp and the time difference in seconds with the current time."""
        if self.last_bmle_execution_time is None:
            return None  # No execution has been recorded yet

        current_time = datetime.datetime.now()
        time_difference = (current_time - self.last_bmle_execution_time).total_seconds()
        return time_difference

    def execute_bmle(self, bmle):

        # Sets the information about the context and the user
        self.context_id = bmle.character
        self.user_id = bmle.id

        # Sets the facial leds
        leds = self.session.service('ALLeds')
        face_color = self.leds_mapping.get(bmle.face.upper(), 0x0000FF00)
        leds.fadeRGB("FaceLeds", face_color, 0.2)

        # Sets the posture
        posture = self.session.service('ALRobotPosture')
        posture.goToPosture(bmle.posture, 0.5)

        # Sets the gestures
        if bmle.gesture == "BORED":
            names, times, keys = bored.names, bored.times, bored.keys
        elif bmle.gesture == "KISSES":
            names, times, keys = kisses.names, kisses.times, kisses.keys
        elif bmle.gesture == "THINKING":
            names, times, keys = thinking.names, thinking.times, thinking.keys
        elif bmle.gesture == "FEAR":
            names, times, keys = fear.names, fear.times, fear.keys
        elif bmle.gesture == "EXCITED":
            names, times, keys = excited.names, excited.times, excited.keys
        elif bmle.gesture == "CHILL":
            names, times, keys = chill.names, chill.times, chill.keys
        elif bmle.gesture == "CURIOUS":
            names, times, keys = curious.names, curious.times, curious.keys
        elif bmle.gesture == "CONFUSED":
            names, times, keys = confused.names, confused.times, confused.keys
        else:
            names, times, keys = happy.names, happy.times, happy.keys

        #if len(names) > 0:
        #    motion = self.session.service('ALMotion')
        #    motion.angleInterpolation(names, keys, times, True)

        # Sets how and what the robot should say
        tone = self.tone_mapping.get(bmle.speech.get('tone', '').upper(), 1.0)
        speed = self.speed_mapping.get(bmle.speech.get('speed', '').upper(), 100)
        volume = self.tone_mapping.get(bmle.speech.get('tone', '').upper(), 1.0)

        tts = self.session.service('ALTextToSpeech')
        tts.setParameter('speed', speed)
        tts.setParameter('pitchShift', tone)
        tts.setVolume(volume)

        aas_configuration = {"bodyLanguageMode":"random"}
        aas = self.session.service('ALAnimatedSpeech')

        # Normalizar el texto antes de enviarlo al robot
        normalized_text = self.normalize_text_for_nao(bmle.speech['text'])
        aas.say(normalized_text)

        #Now we should verify if the robot should listen to the student
        if not bmle.speech.get('end'):
            speech_value = self.speech_service.listen(bmle.gaze)

            if speech_value is not None:
                self.send_speech_recognition(self.user_id, self.context_id, speech_value, self.conversation_queue)
            else:
                error_message = 'No he entendido lo que has dicho. Si sigues necesitando ayuda solicítala a través de Scratch y te ayudaré encantado.'
                aas.say(self.normalize_text_for_nao(error_message))
                print("No speech detected!!")
                self.reset_nao()

        else:
            self.reset_nao()

    def reset_nao(self):

        # Resets the facial leds
        leds = self.session.service('ALLeds')
        leds.fadeRGB("FaceLeds", 0x00FFFFFF, 0.2)

        # Resets the posture
        posture = self.session.service('ALRobotPosture')
        posture.goToPosture('StandInit', 0.5)

        # Once the robot resets, we store the last execution timestamp
        self.last_bmle_execution_time = datetime.datetime.now()


    def send_speech_recognition(self, user_id, context_id, speech_value, conversation_queue):
        try:
            # Creates the response JSON object
            message_data = {
                "userId": user_id,
                "contextId": context_id,
                "userPrompt": speech_value,
                "systemPrompt": ""
            }
            message_json = json.dumps(message_data, ensure_ascii=False)

            # Publish the message to the RabbitMQ queue
            self.channel.basic_publish(
                exchange='',
                routing_key= conversation_queue,
                body=message_json,
                properties=pika.BasicProperties(
                    delivery_mode=2  # Makes the message persistent
                )
            )

            # Print the sent message
            print(f"[x] Message sent to queue '{self.conversation_queue}': {speech_value}")

            #self.memory.unsubscribeToEvent("WordRecognized","NaoService")
            #self.asr.popContexts()

        except Exception as e:
            # Catch and print any error
            print(f"[ERROR] Failed to send message: {str(e)}")