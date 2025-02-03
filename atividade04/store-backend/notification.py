from fastapi import FastAPI, Response
import pika
import json
import asyncio
from defines import (
    e_commerce_queue,
    pedidos_criados_key,
    pagamentos_aprovados_key,
    pagamentos_recusados_key,
    pedidos_enviados_key,
    pedidos_excluidos_key,
    host,
    exchange
)

app = FastAPI()

# Função para consumir eventos do RabbitMQ
def consumir_eventos():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange, exchange_type='direct')

    # Declara as filas e as associa ao exchange
    for routing_key in [pedidos_criados_key, pagamentos_aprovados_key, pagamentos_recusados_key, pedidos_enviados_key, pedidos_excluidos_key]:
        channel.queue_declare(queue=routing_key)
        channel.queue_bind(exchange=exchange, queue=routing_key, routing_key=routing_key)

    # Consome mensagens da fila
    for method_frame, properties, body in channel.consume(queue=pedidos_criados_key):  # Consome apenas um tópico como exemplo
        mensagem = json.loads(body)
        yield mensagem
        channel.basic_ack(method_frame.delivery_tag)

# Endpoint SSE para enviar notificações ao frontend
@app.get("/notificacoes")
async def notificacoes():
    async def event_generator():
        for mensagem in consumir_eventos():
            yield f"data: {json.dumps(mensagem)}\n\n"
            await asyncio.sleep(1)  # Simula um pequeno atraso

    return Response(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)