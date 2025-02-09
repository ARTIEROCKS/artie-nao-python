import qi
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

    def __init__(self):
        self.session = qi.Session()
        self.session.connect("tcp://192.168.0.100:9559")


    def execute_bmle(self, bmle):

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

        return None

    def reset_nao(self):

        # Resets the facial leds
        leds = self.session.service('ALLeds')
        leds.fadeRGB("FaceLeds", 0x00FFFFFF, 0.2)

        return None