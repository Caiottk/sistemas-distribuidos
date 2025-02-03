from flask import Flask, request, jsonify
import pika
import json

app = Flask(__name__)

# Configuração do RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Tópicos
channel.exchange_declare(exchange='pedidos', exchange_type='topic')

# Endpoint para criar pedidos
@app.route('/pedidos', methods=['POST'])
def criar_pedido():
    pedido = request.json
    pedido_id = pedido['id']
    
    # Publicar evento no tópico Pedidos_Criados
    channel.basic_publish(exchange='pedidos', routing_key='Pedidos_Criados', body=json.dumps(pedido))
    
    return jsonify({"status": "Pedido criado", "pedido_id": pedido_id}), 201

# Consumir eventos de Pagamentos_Aprovados
def callback_pagamentos_aprovados(ch, method, properties, body):
    pedido = json.loads(body)
    print(f"Pagamento aprovado para o pedido {pedido['id']}")
    # Atualizar status do pedido

channel.basic_consume(queue='pagamentos_aprovados', on_message_callback=callback_pagamentos_aprovados, auto_ack=True)

# Iniciar o consumidor em uma thread separada
import threading
threading.Thread(target=channel.start_consuming).start()

if __name__ == '__main__':
    app.run(port=5000)