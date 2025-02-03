from flask import Flask, request, jsonify
import pika
import json

app = Flask(__name__)

# Configuração do RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Endpoint para receber webhooks de pagamento
@app.route('/webhook/pagamento', methods=['POST'])
def webhook_pagamento():
    evento = request.json
    status = evento['status']
    pedido_id = evento['pedido_id']
    
    if status == 'aprovado':
        channel.basic_publish(exchange='pedidos', routing_key='Pagamentos_Aprovados', body=json.dumps({"id": pedido_id}))
    elif status == 'recusado':
        channel.basic_publish(exchange='pedidos', routing_key='Pagamentos_Recusados', body=json.dumps({"id": pedido_id}))
    
    return jsonify({"status": "Webhook recebido"}), 200

if __name__ == '__main__':
    app.run(port=5001)