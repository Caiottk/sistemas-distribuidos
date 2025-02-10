from defines import *
from auxFunc import *
import asyncio
import json
import logging

# Configuração básica do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('estoque.log'),  # Salva logs em um arquivo
        logging.StreamHandler()  # Exibe logs no console
    ]
)

class Estoque:
    connection, channel = None, None

    produtos = {
        1: {"id": 1, "name": "Laptop", "price": 1200, "quantity": 20},
        2: {"id": 2, "name": "Mouse", "price": 30, "quantity": 30},
        3: {"id": 3, "name": "Keyboard", "price": 50, "quantity": 40},
    }

    orders = {}

    @staticmethod
    def init() -> None:
        logging.info("Inicializando o serviço de estoque...")
        Estoque.subscribe_to_topics()

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
            channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=get_estoques_key)
            channel.basic_consume(queue=queue_name, on_message_callback=Estoque.on_get_estoque)

            channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_criados_key)
            channel.basic_consume(queue=queue_name, on_message_callback=Estoque.on_pedidos_criados)

            channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_excluidos_key)
            channel.basic_consume(queue=queue_name, on_message_callback=Estoque.on_pedidos_excluidos)

            logging.info("Iniciando consumo de mensagens...")
            channel.start_consuming()
        except Exception as e:
            logging.error(f"Erro ao subscrever aos tópicos: {e}")

    @staticmethod
    def on_get_estoque(ch, method, properties, body):
        try:
            logging.info("Recebida solicitação de estoque...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")

            message = json.loads(body)
            correlation_id = message.get("correlation_id")

            logging.info(f"Enviando estoque para correlation_id: {correlation_id}")
            channel.basic_publish(
                exchange=exchange,
                routing_key=estoques_key,
                body=json.dumps({"produtos": list(Estoque.produtos.values()), "correlation_id": correlation_id}),
            )
            connection.close()

            ch.basic_ack(delivery_tag=method.delivery_tag)
            logging.info("Estoque enviado com sucesso.")
            return True
        except Exception as e:
            logging.error(f"Erro ao publicar estoque: {e}")
            return False

    @staticmethod
    def on_pedidos_criados(ch, method, properties, body):
        try:
            logging.info("Recebido novo pedido criado...")
            message = json.loads(body.decode('utf-8'))
            if "order" in message.keys():
                correlation_id = message['correlation_id']
                Estoque.orders[correlation_id] = message["order"]
                logging.info(f"Pedido {correlation_id} adicionado ao sistema de estoque.")

                for item in message["order"]["cart"]:
                    produto_id = item["id"]
                    quantidade = item["quantity"]
                    Estoque.produtos[produto_id]["quantity"] -= quantidade
                    logging.info(f"Quantidade do produto {produto_id} atualizada. Nova quantidade: {Estoque.produtos[produto_id]['quantity']}")
        except Exception as e:
            logging.error(f"Erro ao processar pedido criado: {e}")

    @staticmethod
    def on_pedidos_excluidos(ch, method, properties, body):
        try:
            logging.info("Recebido pedido excluído...")
            message = json.loads(body.decode('utf-8'))
            correlation_id = message['correlation_id']

            if correlation_id in Estoque.orders.keys():
                orders = Estoque.orders[correlation_id]
                for item in orders["cart"]:
                    produto_id = item["id"]
                    quantidade = item["quantity"]
                    Estoque.produtos[produto_id]["quantity"] += quantidade
                    logging.info(f"Quantidade do produto {produto_id} restaurada. Nova quantidade: {Estoque.produtos[produto_id]['quantity']}")

                del Estoque.orders[correlation_id]
                logging.info(f"Pedido {correlation_id} removido do sistema de estoque.")
        except Exception as e:
            logging.error(f"Erro ao processar pedido excluído: {e}")

    @staticmethod
    def run() -> None:
        logging.info("Serviço de estoque em execução...")
        while True:
            pass

if __name__ == "__main__":
    Estoque.init()
    Estoque.run()