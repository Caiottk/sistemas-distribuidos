import pika
import json

# Configuração do RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Consumir eventos de Pedidos_Criados
def callback_pedidos_criados(ch, method, properties, body):
    pedido = json.loads(body)
    print(f"Atualizando estoque para o pedido {pedido['id']}")
    # Lógica para atualizar o estoque

channel.basic_consume(queue='pedidos_criados', on_message_callback=callback_pedidos_criados, auto_ack=True)

# Consumir eventos de Pedidos_Excluídos
def callback_pedidos_excluidos(ch, method, properties, body):
    pedido = json.loads(body)
    print(f"Revertendo estoque para o pedido {pedido['id']}")
    # Lógica para reverter o estoque

channel.basic_consume(queue='pedidos_excluidos', on_message_callback=callback_pedidos_excluidos, auto_ack=True)

# Iniciar o consumidor
channel.start_consuming()