from defines import *
from auxFunc import *
import json
import threading

class Entrega:
    connection,channel = None,None
    orders = []

    def subscribe_to_topics():

        # Start consuming messages from topic_a
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange, exchange_type="topic")

        # Declare a queue for topic_a and bind it to the exchange
        result = channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pagamentos_aprovados_key)
        channel.basic_consume(queue=queue_name, on_message_callback=Entrega.on_pagamentos_aprovados)

        channel.start_consuming()

        orders = []

    def processar_envios():
        while True:
            while len(Entrega.orders) == 0:
                pass
            order = Entrega.orders.pop(0)
            Entrega.publish_pedidos_enviados(order)

    def on_pagamentos_aprovados(ch, method, properties, body):
        """Se algum pedido for aprovado, ele envia o pedido (publica no tópico pedidos enviados)"""
        message = json.loads(body.decode('utf-8'))
        Entrega.orders.append(message)

    def publish_pedidos_enviados(message:dict)->bool:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")
            channel.basic_publish(
                exchange=exchange,
                routing_key=pagamentos_recusados_key,
                body=json.dumps(message),
            )
            connection.close()

            print("Pagamento Recusado publicado com sucesso")
            return True
        except Exception as e:
            print(f"Erro ao publicar Pagamento Recusado\n{e}")
            return False

    def run()->None:
        while True:
            pass

threading.Thread(target=Entrega.subscribe_to_topics, daemon=True).start()
threading.Thread(target=Entrega.processar_envios, daemon=True).start()

if __name__ == "__main__":
    Entrega.subscribe_to_topics()
    Entrega.run()