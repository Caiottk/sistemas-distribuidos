from defines import *
from auxFunc import *
import asyncio
import json

class Estoque:
    connection,channel = None,None

        # Sample product data
    produtos = [
        {"id": 1, "name": "Laptop", "price": 1200},
        {"id": 2, "name": "Mouse", "price": 30},
        {"id": 3, "name": "Keyboard", "price": 50},
    ]

    produtos = {
        1: {"id": 1,"name": "Laptop", "price": 1200,"quantity":20},
        2: {"id": 2,"name": "Mouse", "price": 30,"quantity":30},
        3: {"id": 3,"name": "Keyboard", "price": 50,"quantity":40},
    }


    orders = {}

    def init()->None:
        Estoque.subscribe_to_topics()

    def subscribe_to_topics():

        # Start consuming messages from topic_a
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange, exchange_type="topic")

        # Declare a queue for topic_a and bind it to the exchange
        result = channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=get_estoques_key)
        channel.basic_consume(queue=queue_name, on_message_callback=Estoque.on_get_estoque)

        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_criados_key)
        channel.basic_consume(queue=queue_name, on_message_callback=Estoque.on_pedidos_criados)

        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_excluidos_key)
        channel.basic_consume(queue=queue_name, on_message_callback=Estoque.on_pedidos_excluidos)

        channel.start_consuming()


    def on_get_estoque(ch, method, properties, body):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")

            # Parse the incoming message
            message = json.loads(body)
            correlation_id = message.get("correlation_id")

            # Publish the response to the estoques_key routing key
            channel.basic_publish(
                exchange=exchange,
                routing_key=estoques_key,
                body=json.dumps({"produtos": list(Estoque.produtos.values()), "correlation_id": correlation_id}),
            )
            connection.close()

            ch.basic_ack(delivery_tag=method.delivery_tag)
            print("Estoque enviado com Sucesso")
            return True
        except Exception as e:
            print(f"Erro ao publicar estoque:\n{e}")
            return False
    
    def on_pedidos_criados(ch, method, properties, body):
        """TODOOO Sistema de Estoque!!!"""
        message = json.loads(body.decode('utf-8'))
        Estoque.orders[message['correlation_id']] = message["order"]
        for item in message["order"]["cart"]:
            Estoque.produtos[item["id"]]["quantity"] -= item["quantity"]
        
    def on_pedidos_excluidos(ch, method, properties, body):
        """TODOOO Sistema de Estoque!!!"""
        message = json.loads(body.decode('utf-8'))
        if message['correlation_id'] in Estoque.orders.keys():
            orders = Estoque.orders[message['correlation_id']]
            for item in orders["cart"]:
                Estoque.produtos[item["id"]]["quantity"] += item["quantity"]
            del Estoque.orders[message['correlation_id']]
        print("Pedido Excluido")
        print(message)
    

    def run()->None:
        while True:
            pass

if __name__ == "__main__":
    Estoque.init()
    Estoque.run()