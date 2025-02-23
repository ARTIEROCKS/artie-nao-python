import pika
import os
from service.bmle_service import BMLService
from service.nao_service import NAOService

# Function to consume the queue
def start_consuming():
    # Getting the connection data from the environment variables
    rabbitmq_host = os.getenv('APP_RABBITMQ_HOST', 'localhost')
    rabbitmq_port = os.getenv('APP_RABBITMQ_PORT', 5672)
    rabbitmq_user = os.getenv('APP_RABBITMQ_USER', 'user')
    rabbitmq_password = os.getenv('APP_RABBITMQ_PASSWORD', 'password')
    rabbitmq_vhost = os.getenv('APP_RABBITMQ_VHOST', '/')
    pedagogical_interventions_queue = os.getenv('APP_RABBITMQ_INTERVENTIONS_QUEUE', '')
    conversations_queue = os.getenv('APP_RABBITMQ_CONVERSATIONS_QUEUE','')
    interventions_waiting_time = os.getenv('APP_INTERVENTIONS_WAITING_TIME', 60)

    # Environment variables about the Robot
    robot_address = os.getenv('APP_ROBOT_ADDRESS', 'tcp://192.168.0.102:9559')


    # RabbitMQ connection
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    parameters = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, virtual_host=rabbitmq_vhost,
                                           credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Creation of the queues if it doesn't exist
    channel.queue_declare(queue=pedagogical_interventions_queue, durable=True, auto_delete=False)
    channel.queue_declare(queue=conversations_queue, durable=True, auto_delete=False)

    # BML Service
    bml_service = BMLService()

    # NAO Service
    nao_service = NAOService(channel, conversations_queue, robot_address)

    # Subscription to the queue
    channel.basic_consume(queue=pedagogical_interventions_queue,
                          on_message_callback=lambda ch, method, properties, body: callback(ch, method, properties,
                                                                                            body, bml_service, nao_service,
                                                                                            interventions_waiting_time))

    # Waiting for new messages
    print('Waiting for new messages...')
    channel.start_consuming()


# Function to process the message queue
def callback(ch, method, properties, body, bmle_service, nao_service, interventions_waiting_time):
    print("Getting a new BMLe...")

    try:
        # Checks if the waiting time has been reached or not
        if (nao_service.get_last_execution_time_difference() is None or
                nao_service.get_last_execution_time_difference() >= 0): #int(interventions_waiting_time)):
            bmle = bmle_service.deserialize(body)
            nao_service.execute_bmle(bmle)
        else:
            print("The waiting time between interactions has not yet been reached.")
    except Exception as e:
        print(f"We had an error when processing the BMLe: {e}")

    # Remove the message from the queue
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print("BMLe ACKed!")