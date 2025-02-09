from service import queue_service
from threading import Thread
# import qi

if __name__ == "__main__":

    # We get the environment
    t = Thread(target=queue_service.start_consuming)
    t.start()

    # Tests
    #session = qi.Session()
    #session.connect("tcp://192.168.0.100:9559")
    #tts = session.service("ALTextToSpeech")
    #tts.say("hello")