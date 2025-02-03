from flask import Flask, Response
import pika
import json

app = Flask(__name__)

# Configuração do RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Função para enviar notificações via SSE
def gerar_notificacao(pedido_id, status):
    return f"data: {json.dumps({'pedido_id': pedido_id, 'status': status})}\n\n"

# Consumir eventos de todos os tópicos
def callback_notificacoes(ch, method, properties, body):
    evento = json.loads(body)
    pedido_id = evento['id']
    status = method.routing_key
    
    # Enviar notificação via SSE
    return Response(gerar_notificacao(pedido_id, status), content_type='text/event-stream')

channel.basic_consume(queue='notificacoes', on_message_callback=callback_notificacoes, auto_ack=True)

# Iniciar o consumidor em uma thread separada
import threading
threading.Thread(target=channel.start_consuming).start()

if __name__ == '__main__':
    app.run(port=5002)