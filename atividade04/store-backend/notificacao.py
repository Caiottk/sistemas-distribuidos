from defines import *
from auxFunc import *
import asyncio
import json
import threading

class Notificacao:
    connection,channel = None,None

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
        print(message)
    

    def run()->None:
        while True:
            pass

threading.Thread(target=Notificacao.subscribe_to_topics, daemon=True).start()

if __name__ == "__main__":
    Notificacao.init()
    Notificacao.run()