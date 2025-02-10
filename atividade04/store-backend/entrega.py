from defines import *
from auxFunc import *
import json
import threading
import time
import asyncio
import logging

# Configuração básica do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('entrega.log'),
        logging.StreamHandler()
    ]
)

class Entrega:
    connection, channel = None, None
    orders = []

    @staticmethod
    def subscribe_to_topics():
        try:
            logging.info("Iniciando subscribe_to_topics...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")

            result = channel.queue_declare(queue="", exclusive=True)
            queue_name = result.method.queue
            channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pagamentos_aprovados_key)
            channel.basic_consume(queue=queue_name, on_message_callback=Entrega.on_pagamentos_aprovados)

            logging.info("Consumindo mensagens do tópico pagamentos_aprovados...")
            channel.start_consuming()

            Entrega.orders = []
        except Exception as e:
            logging.error(f"Erro ao subscrever aos tópicos: {e}")

    @staticmethod
    def processar_envios():
        logging.info("Iniciando processar_envios...")
        while True:
            while len(Entrega.orders) == 0:
                time.sleep(1)
            order = Entrega.orders.pop(0)
            logging.info(f"Processando envio do pedido: {order}")
            Entrega.publish_pedidos_enviados(order)

    @staticmethod
    def on_pagamentos_aprovados(ch, method, properties, body):
        try:
            logging.info("Nova mensagem recebida em pagamentos_aprovados")
            message = json.loads(body.decode('utf-8'))
            message["status"] = "Enviado"
            time.sleep(5)
            Entrega.orders.append(message)
            logging.info(f"Pedido aprovado adicionado à fila de envios: {message}")
        except Exception as e:
            logging.error(f"Erro ao processar mensagem de pagamentos_aprovados: {e}")

    @staticmethod
    def publish_pedidos_enviados(message: dict) -> bool:
        try:
            logging.info(f"Publicando pedido enviado: {message}")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")
            channel.basic_publish(
                exchange=exchange,
                routing_key=pedidos_enviados_key,
                body=json.dumps(message),
            )
            connection.close()

            logging.info("Pedido Enviado publicado com sucesso")
            return True
        except Exception as e:
            logging.error(f"Erro ao publicar Pedido Enviado: {e}")
            return False

    @staticmethod
    def run() -> None:
        logging.info("Iniciando execução do serviço de entrega...")
        while True:
            time.sleep(1)

# Iniciando threads
threading.Thread(target=Entrega.subscribe_to_topics, daemon=True).start()
threading.Thread(target=Entrega.processar_envios, daemon=True).start()

if __name__ == "__main__":
    Entrega.subscribe_to_topics()
    Entrega.run()