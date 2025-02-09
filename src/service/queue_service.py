import pika
import os
from service.bmle_service import BMLService
from service.nao_service import NAOService

# Function to consume the queue
def start_consuming():
    # Getting the connection data from the environment variables
    rabbitmq_host = os.getenv('APP_RABBITMQ_HOST', 'localhost')
    rabbitmq_port = os.getenv('APP_RABBITMQ_PORT', 5672)
    rabbitmq_user = os.getenv('APP_RABBITMQ_USER', 'artie')
    rabbitmq_password = os.getenv('APP_RABBITMQ_PASSWORD', 'ArtiE28130000')
    rabbitmq_vhost = os.getenv('APP_RABBITMQ_VHOST', '/')
    rabbitmq_queue = 'pedagogicalInterventions'

    # RabbitMQ connection
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    parameters = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, virtual_host=rabbitmq_vhost,
                                           credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Creation of the queue if it doesn't exist
    channel.queue_declare(queue=rabbitmq_queue, durable=True, auto_delete=False)

    # BML Service
    bml_service = BMLService()

    # NAO Service
    nao_service = NAOService()

    # Subscription to the queue
    channel.basic_consume(queue=rabbitmq_queue,
                          on_message_callback=lambda ch, method, properties, body: callback(ch, method, properties,
                                                                                            body, bml_service, nao_service))

    # Waiting for new messages
    print('Waiting for new messages...')
    channel.start_consuming()


# Function to process the message queue
def callback(ch, method, properties, body, bmle_service, nao_service):
    print("Getting a new BMLe...")

    try:
        bmle = bmle_service.deserialize(body)
        nao_service.execute_bmle(bmle)
    except Exception as e:
        print(f"We had an error when processing the BMLe: {e}")

    # Remove the message from the queue
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print("BMLe ACKed!")