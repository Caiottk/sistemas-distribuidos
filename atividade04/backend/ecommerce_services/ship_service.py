import pika
import json

# Configuração do RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Consumir eventos de Pagamentos_Aprovados
def callback_pagamentos_aprovados(ch, method, properties, body):
    pedido = json.loads(body)
    print(f"Preparando entrega para o pedido {pedido['id']}")
    # Lógica para preparar a entrega
    channel.basic_publish(exchange='pedidos', routing_key='Pedidos_Enviados', body=json.dumps(pedido))

channel.basic_consume(queue='pagamentos_aprovados', on_message_callback=callback_pagamentos_aprovados, auto_ack=True)

# Iniciar o consumidor
channel.start_consuming()