from defines import *
from auxFunc import *
import json
import requests
import threading
import time
import asyncio

class Pagamento:
    connection,channel = None,None
    orders = []

    def subscribe_to_topics()->None:
        # Start consuming messages from topic_a
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange, exchange_type="topic")

        # Declare a queue for topic_a and bind it to the exchange
        result = channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_criados_key)
        channel.basic_consume(queue=queue_name, on_message_callback=Pagamento.on_pedidos_criados)

        channel.start_consuming()

    def processar_pagamentos():
        while True:
            while len(Pagamento.orders)==0:
                time.sleep(1)
            time.sleep(1)
            order = Pagamento.orders.pop(0)
            order_info = order["order"]
            url = "http://0.0.0.0:8000/payment"
            print(order['order'])
            response = requests.post(url, json=order['order'])
            if response.status_code == 200:
                print("Payment successful!")
                print("Response:", response.json())
               
                response = response.json()
                print(type(response["Aproved"]))
                if response["Aproved"]:
                    order["status"] = "Aprovado"
                    Pagamento.publish_pagamentos_aprovados(order)
                else:
                    order["status"] = "Recusado"
                    Pagamento.publish_pagamentos_recusados(order)
            else:
                print("Payment failed!")
                print("Status Code:", response.status_code)
                print("Error:", response.json())
                #Pagamento.orders.append(order)
                time.sleep(10)

    def on_pedidos_criados(ch, method, properties, body):
        """TODOO: Pedido Criado"""
        message = json.loads(body.decode('utf-8'))
        Pagamento.orders.append(message)
     
    
    def publish_pagamentos_recusados(message:dict)->bool:
        """Formato do Json de Pedidos:
            "id_pedido": int
        """
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

    def publish_pagamentos_aprovados(message:dict)->bool:
        """Formato do Json de Pedidos:
            "id_pedido": int
        """
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")
            channel.basic_publish(
                exchange=exchange,
                routing_key=pagamentos_aprovados_key,
                body=json.dumps(message),
            )
            connection.close()

            print("Pagamento Aprovado publicado com sucesso")
            return True
        except Exception as e:
            print(f"Erro ao publicar Pagamento Recusado\n{e}")
            return False

    def run()->None:
        while True:
            pass

threading.Thread(target=Pagamento.subscribe_to_topics, daemon=True).start()
threading.Thread(target=Pagamento.processar_pagamentos, daemon=True).start()

if __name__ == "__main__":
    Pagamento.run()