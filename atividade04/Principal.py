import json
import asyncio
import pika
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Sample product data
PRODUCTS = [
    {"id": 1, "name": "Laptop", "price": 1200},
    {"id": 2, "name": "Mouse", "price": 30},
    {"id": 3, "name": "Keyboard", "price": 50},
]

# RabbitMQ Connection Parameters
RABBITMQ_HOST = "localhost"
EXCHANGE_NAME = "e_commerce"
QUEUE_NAME = "e_commerce_queue"
ROUTING_KEY = "order"


# 📌 Define Model for Order Data
class Order(BaseModel):
    product_id: int
    quantity: int


# ✅ Endpoint: Get List of Products
@app.get("/products")
async def get_products():
    return {"products": PRODUCTS}


# ✅ Endpoint: Place Order (Publish Message)
@app.post("/order")
async def place_order(order: Order):
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()

    # Declare Exchange and Queue
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="direct", durable=True)
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=ROUTING_KEY)

    # Publish Order Message
    message = json.dumps({"product_id": order.product_id, "quantity": order.quantity})
    channel.basic_publish(
        exchange=EXCHANGE_NAME,
        routing_key=ROUTING_KEY,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2),
    )

    connection.close()
    return {"message": "Order placed successfully!"}


# 🔁 RabbitMQ Consumer Class
class RabbitMQConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None

    async def connect(self):
        loop = asyncio.get_running_loop()
        connection_params = pika.ConnectionParameters(host=RABBITMQ_HOST, heartbeat=600, blocked_connection_timeout=300)

        self.connection = await loop.run_in_executor(None, lambda: pika.BlockingConnection(connection_params))
        self.channel = self.connection.channel()

        # Declare Exchange and Queue
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="direct", durable=True)
        self.channel.queue_declare(queue=QUEUE_NAME, durable=True)
        self.channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=ROUTING_KEY)

        # Consume Messages
        self.channel.basic_consume(queue=QUEUE_NAME, on_message_callback=self.callback, auto_ack=True)
        print("[*] Waiting for messages...")
        await loop.run_in_executor(None, self.channel.start_consuming)

    def callback(self, ch, method, properties, body):
        order = json.loads(body)
        print(f"✅ Order Received: {order}")


# ✅ Run Consumer in Background
consumer = RabbitMQConsumer()


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consumer.connect())


# Run FastAPI with:
# uvicorn Principal:app --reload
