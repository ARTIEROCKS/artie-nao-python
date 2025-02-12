import qi
import pika
import time
import datetime
import json
from motion import bored, happy, kisses, thinking, fear, excited, chill, curious, confused

class NAOService:

    tone_mapping = {
        "HIGH": 1.25,
        "LOW": 1.0
    }
    speed_mapping = {
        "HIGH": 150,
        "LOW": 100
    }
    leds_mapping ={
        "HAPPY": 0x0000FF00, # Green
        "ANGRY": 0x00FFFF00, # Yellow
        "CONTEMPT": 0x000000FF, # Blue
        "NEUTRAL": 0x00FFFFFF # White
    }
    vocabulary = ["si", "no"]

    def __init__(self, queue_channel=None, conversation_queue=None, robot_address=None):
        self.context_id = None
        self.user_id = None
        self.channel = queue_channel
        self.conversation_queue = conversation_queue
        self.last_bmle_execution_time = None  # Stores the last execution timestamp

        # Attempt to connect with retry mechanism
        self.session = self.connect_with_retry(robot_address=robot_address)

    def connect_with_retry(self, max_retries=5, delay=5, robot_address = None):
        """Attempts to connect to the NAO robot, retrying in case of failure."""
        for attempt in range(max_retries):
            try:
                session = qi.Session()
                session.connect(robot_address)
                print("Successfully connected to NAO.")
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
        names, times, keys = list()
        if bmle.gesture.upper() == "BORED":
            names, times, keys = bored.names, bored.times, bored.keys
        elif bmle.gesture.upper() == "KISSES":
            names, times, keys = kisses.names, kisses.times, kisses.keys
        elif bmle.gesture.upper() == "THINKING":
            names, times, keys = thinking.names, thinking.times, thinking.keys
        elif bmle.gesture.upper() == "FEAR":
            names, times, keys = fear.names, fear.times, fear.keys
        elif bmle.gesture.upper() == "EXCITED":
            names, times, keys = excited.names, excited.times, excited.keys
        elif bmle.gesture.upper() == "CHILL":
            names, times, keys = chill.names, chill.times, chill.keys
        elif bmle.gesture.upper() == "CURIOUS":
            names, times, keys = curious.names, curious.times, curious.keys
        elif bmle.gesture.upper() == "CONFUSED":
            names, times, keys = confused.names, confused.times, confused.keys
        else:
            names, times, keys = happy.names, happy.times, happy.keys

        if names.count() > 0:
            motion = self.session.service('ALMotion')
            motion.angleInterpolation(names, keys, times, True)

        # Sets how and what the robot should say
        tone = self.tone_mapping.get(bmle.speech.get('tone', '').upper(), 1.0)
        speed = self.speed_mapping.get(bmle.speech.get('speed', '').upper(), 100)
        volume = self.tone_mapping.get(bmle.speech.get('tone', '').upper(), 1.0)

        tts = self.session.service('ALTextToSpeech')
        tts.setParameter('speed', speed)
        tts.setParameter('pitchShift', tone)
        tts.setVolume(volume)
        tts.say(bmle.speech['text'])

        #Now we should verify if the robot should listen to the student
        if not bmle.speech.get('end'):
            asr = self.session.service('ALSpeechRecognition')
            asr.setLanguage('Spanish')
            asr.setVocabulary(self.vocabulary, False)

            # Adds a bip when robot starts listening
            asr.setAudioExpression(True)

            # Start the subscription and the ends the subscription.
            memory = self.session.service('ALMemory')
            memory.subscriber('WordRecognized').signal.connect(self.speech_recognition)
        else:
            self.reset_nao()

    def reset_nao(self):

        # Resets the facial leds
        leds = self.session.service('ALLeds')
        leds.fadeRGB("FaceLeds", 0x00FFFFFF, 0.2)

        # Resets the posture
        posture = self.session.service('ALRobotPosture')
        posture.goToPosture('Stand', 0.5)

        # Once the robot resets, we store the last execution timestamp
        self.last_bmle_execution_time = datetime.datetime.now()


    def speech_recognition(self, eventName, value, subscriberIdentifier):
        try:

            # Creates the response JSON object
            message_data = {
                "userId": self.user_id,
                "contextId": self.context_id,
                "message": value,
                "prompt": ""
            }
            message_json = json.dumps(message_data, ensure_ascii=False)

            # Publish the message to the RabbitMQ queue
            self.channel.basic_publish(
                exchange='',
                routing_key=self.conversation_queue,
                body=message_json,
                properties=pika.BasicProperties(
                    delivery_mode=2  # Makes the message persistent
                )
            )

            # Print the sent message
            print(f"[x] Message sent to queue '{self.conversation_queue}': {value}")

        except Exception as e:
            # Catch and print any error
            print(f"[ERROR] Failed to send message: {str(e)}")