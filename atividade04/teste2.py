import json
import pika

RABBITMQ_HOST = "localhost"
REQUEST_QUEUE = "get_products"
RESPONSE_QUEUE = "products"

# Sample product list
products = [
    {"id": 1, "name": "Laptop", "price": 1000},
    {"id": 2, "name": "Mouse", "price": 50},
    {"id": 3, "name": "Keyboard", "price": 80}
]

# Establish RabbitMQ connection
connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
channel = connection.channel()

# Declare queues
channel.queue_declare(queue=REQUEST_QUEUE, durable=True)
channel.queue_declare(queue=RESPONSE_QUEUE, durable=True)

def callback(ch, method, properties, body):
    """Send product list when a request is received."""
    print("Received request for products")
    
    # Send product list to "products" queue
    channel.basic_publish(
        exchange='',
        routing_key=RESPONSE_QUEUE,
        body=json.dumps(products)
    )
    print("Sent product list")

# Start consuming messages from "get_products" queue
channel.basic_consume(queue=REQUEST_QUEUE, on_message_callback=callback, auto_ack=True)
print("Waiting for requests on 'get_products' queue...")
channel.start_consuming()
