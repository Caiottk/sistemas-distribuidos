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
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

class Notificacao:
    connection,channel = None,None
    order = []
    def subscribe_to_topics():

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange, exchange_type="topic")

        result = channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_excluidos_key)
        channel.basic_consume(queue=queue_name, on_message_callback=Notificacao.on_pedidos_excluidos)


        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pagamentos_aprovados_key)
        channel.basic_consume(queue=queue_name, on_message_callback=Notificacao.on_pedidos_aprovados)

        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_enviados_key)
        channel.basic_consume(queue=queue_name, on_message_callback=Notificacao.on_pedidos_enviados)


        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_criados_key)
        channel.basic_consume(queue=queue_name, on_message_callback=Notificacao.on_pedidos_criados)
        channel.start_consuming()
    def on_pedidos_criados(ch, method, properties, body):
        message = json.loads(body.decode('utf-8'))
        Notificacao.order.append(message)
        print(message)

    def on_pedidos_enviados(ch, method, properties, body):
        message = json.loads(body.decode('utf-8'))
        Notificacao.order.append(message)
        print(message)

    def on_pedidos_aprovados(ch, method, properties, body):
        message = json.loads(body.decode('utf-8'))
        Notificacao.order.append(message)
        print(message)

    def on_pedidos_excluidos(ch, method, properties, body):
        """TODOOO Sistema de Estoque!!!"""
        message = json.loads(body.decode('utf-8'))
        Notificacao.order.append(message)
        print(message)

    async def generate_order_updates():
        order_id = 1
        flag = False
        status = "Processing"
        while True:
            # Simulate an order status update
            while len(Notificacao.order) == 0:
                await asyncio.sleep(0.1)
            order = Notificacao.order.pop(0)

            order = {
                "order_id": order["correlation_id"],
                "status": order["status"]
            }

            yield f"data: {json.dumps(order)}\n\n"

    @app.get("/notificacao")
    async def sse():
        return StreamingResponse(
            Notificacao.generate_order_updates(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    
threading.Thread(target=Notificacao.subscribe_to_topics, daemon=True).start()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)