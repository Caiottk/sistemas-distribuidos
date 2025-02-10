from defines import *
from auxFunc import *
import json
import requests
import threading
import time
import asyncio
import logging

# Configuração básica do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pagamento.log'),  # Salva logs em um arquivo
        logging.StreamHandler()  # Exibe logs no console
    ]
)

class Pagamento:
    connection, channel = None, None
    orders = []

    @staticmethod
    def subscribe_to_topics() -> None:
        try:
            logging.info("Conectando ao RabbitMQ e subscrevendo aos tópicos...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")

            result = channel.queue_declare(queue="", exclusive=True)
            queue_name = result.method.queue
            channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_criados_key)
            channel.basic_consume(queue=queue_name, on_message_callback=Pagamento.on_pedidos_criados)

            logging.info("Iniciando consumo de mensagens...")
            channel.start_consuming()
        except Exception as e:
            logging.error(f"Erro ao subscrever aos tópicos: {e}")

    @staticmethod
    def processar_pagamentos():
        logging.info("Iniciando processamento de pagamentos...")
        while True:
            while len(Pagamento.orders) == 0:
                time.sleep(1)
            time.sleep(1)
            order = Pagamento.orders.pop(0)
            order_info = order["order"]
            url = "http://127.0.0.1:8000/payment"
            logging.info(f"Processando pagamento para o pedido: {order_info}")

            try:
                response = requests.post(url, json=order['order'])
                if response.status_code == 200:
                    logging.info("Pagamento processado com sucesso!")
                    logging.info(f"Resposta: {response.json()}")

                    response_data = response.json()
                    if response_data["Aproved"]:
                        order["status"] = "Aprovado"
                        logging.info(f"Pagamento aprovado para o pedido: {order_info}")
                        Pagamento.publish_pagamentos_aprovados(order)
                    else:
                        order["status"] = "Recusado"
                        logging.info(f"Pagamento recusado para o pedido: {order_info}")
                        Pagamento.publish_pagamentos_recusados(order)
                else:
                    logging.error(f"Falha no pagamento! Código de status: {response.status_code}")
                    logging.error(f"Erro: {response.json()}")
                    time.sleep(10)
            except Exception as e:
                logging.error(f"Erro ao processar pagamento: {e}")

    @staticmethod
    def on_pedidos_criados(ch, method, properties, body):
        try:
            message = json.loads(body.decode('utf-8'))
            logging.info(f"Recebido novo pedido criado: {message}")
            Pagamento.orders.append(message)
        except Exception as e:
            logging.error(f"Erro ao processar pedido criado: {e}")

    @staticmethod
    def publish_pagamentos_recusados(message: dict) -> bool:
        try:
            logging.info(f"Publicando pagamento recusado: {message}")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")
            channel.basic_publish(
                exchange=exchange,
                routing_key=pagamentos_recusados_key,
                body=json.dumps(message),
            )
            connection.close()

            logging.info("Pagamento Recusado publicado com sucesso")
            return True
        except Exception as e:
            logging.error(f"Erro ao publicar Pagamento Recusado: {e}")
            return False

    @staticmethod
    def publish_pagamentos_aprovados(message: dict) -> bool:
        try:
            logging.info(f"Publicando pagamento aprovado: {message}")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")
            channel.basic_publish(
                exchange=exchange,
                routing_key=pagamentos_aprovados_key,
                body=json.dumps(message),
            )
            connection.close()

            logging.info("Pagamento Aprovado publicado com sucesso")
            return True
        except Exception as e:
            logging.error(f"Erro ao publicar Pagamento Aprovado: {e}")
            return False

    @staticmethod
    def run() -> None:
        logging.info("Serviço de pagamento em execução...")
        while True:
            pass

# Iniciando threads
threading.Thread(target=Pagamento.subscribe_to_topics, daemon=True).start()
threading.Thread(target=Pagamento.processar_pagamentos, daemon=True).start()

if __name__ == "__main__":
    Pagamento.run()