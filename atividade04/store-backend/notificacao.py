from defines import *
from auxFunc import *
import asyncio
import json
import threading
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.responses import StreamingResponse
import uvicorn

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from this origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

class Notificacao:
    connection,channel = None,None
    order = []
    def subscribe_to_topics():

        # Start consuming messages from topic_a
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange, exchange_type="topic")

        # Declare a queue for topic_a and bind it to the exchange
        result = channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_excluidos_key)
        channel.basic_consume(queue=queue_name, on_message_callback=Notificacao.on_pedidos_excluidos)

        channel.start_consuming()

    def on_pedidos_excluidos(ch, method, properties, body):
        """TODOOO Sistema de Estoque!!!"""
        message = json.loads(body.decode('utf-8'))
        Notificacao.order.append(message)
        print(message)

    # Simulated function to generate order updates
    async def generate_order_updates():
        order_id = 1
        flag = False
        status = "Processing"
        while True:
            # Simulate an order status update
            

            order = {
                "order_id": "aaa",
                "status": "bb"
            }

            yield f"data: {json.dumps(order)}\n\n"
            #await asyncio.sleep(1)  # Simulate a delay between updates

    @app.get("/notificacao")
    async def sse():
        # Return a StreamingResponse for SSE
        return StreamingResponse(
            Notificacao.generate_order_updates(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    
# Start the RabbitMQ consumer in a separate thread
threading.Thread(target=Notificacao.subscribe_to_topics, daemon=True).start()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)