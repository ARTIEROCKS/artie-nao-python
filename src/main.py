from service import queue_service
from threading import Thread

if __name__ == "__main__":

    #We get the environment
    t = Thread(target=queue_service.start_consuming)
    t.start()

