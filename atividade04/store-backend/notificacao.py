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
import logging

# Configuração básica do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('notificacao.log'),  # Salva logs em um arquivo
        logging.StreamHandler()  # Exibe logs no console
    ]
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

class Notificacao:
    connection, channel = None, None
    order = []

    @staticmethod
    def subscribe_to_topics():
        try:
            logging.info("Conectando ao RabbitMQ e subscrevendo aos tópicos...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")

            result = channel.queue_declare(queue="", exclusive=True)
            queue_name = result.method.queue

            # Subscrevendo aos tópicos
            channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_excluidos_key)
            channel.basic_consume(queue=queue_name, on_message_callback=Notificacao.on_pedidos_excluidos)

            channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pagamentos_aprovados_key)
            channel.basic_consume(queue=queue_name, on_message_callback=Notificacao.on_pedidos_aprovados)

            channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_enviados_key)
            channel.basic_consume(queue=queue_name, on_message_callback=Notificacao.on_pedidos_enviados)

            channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_criados_key)
            channel.basic_consume(queue=queue_name, on_message_callback=Notificacao.on_pedidos_criados)

            logging.info("Iniciando consumo de mensagens...")
            channel.start_consuming()
        except Exception as e:
            logging.error(f"Erro ao subscrever aos tópicos: {e}")

    @staticmethod
    def on_pedidos_criados(ch, method, properties, body):
        try:
            message = json.loads(body.decode('utf-8'))
            logging.info(f"Recebido novo pedido criado: {message}")
            Notificacao.order.append(message)
        except Exception as e:
            logging.error(f"Erro ao processar pedido criado: {e}")

    @staticmethod
    def on_pedidos_enviados(ch, method, properties, body):
        try:
            message = json.loads(body.decode('utf-8'))
            logging.info(f"Recebido pedido enviado: {message}")
            Notificacao.order.append(message)
        except Exception as e:
            logging.error(f"Erro ao processar pedido enviado: {e}")

    @staticmethod
    def on_pedidos_aprovados(ch, method, properties, body):
        try:
            message = json.loads(body.decode('utf-8'))
            logging.info(f"Recebido pedido aprovado: {message}")
            Notificacao.order.append(message)
        except Exception as e:
            logging.error(f"Erro ao processar pedido aprovado: {e}")

    @staticmethod
    def on_pedidos_excluidos(ch, method, properties, body):
        try:
            message = json.loads(body.decode('utf-8'))
            logging.info(f"Recebido pedido excluído: {message}")
            Notificacao.order.append(message)
        except Exception as e:
            logging.error(f"Erro ao processar pedido excluído: {e}")

    @staticmethod
    async def generate_order_updates():
        logging.info("Iniciando geração de atualizações de pedidos...")
        while True:
            while len(Notificacao.order) == 0:
                await asyncio.sleep(0.1)
            order = Notificacao.order.pop(0)
            logging.info(f"Enviando atualização de pedido: {order}")

            order = {
                "order_id": order["correlation_id"],
                "status": order.get("status", "Processing")
            }

            yield f"data: {json.dumps(order)}\n\n"

    @app.get("/notificacao")
    async def sse():
        logging.info("Nova conexão SSE estabelecida.")
        return StreamingResponse(
            Notificacao.generate_order_updates(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    
# Iniciando a thread para consumir mensagens do RabbitMQ
threading.Thread(target=Notificacao.subscribe_to_topics, daemon=True).start()

if __name__ == "__main__":
    logging.info("Iniciando servidor FastAPI...")
    uvicorn.run(app, host="0.0.0.0", port=8001)