from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pika
import json
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

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample product list
products = [
    {"id": 1, "name": "Laptop", "price": 1000},
    {"id": 2, "name": "Smartphone", "price": 500},
    {"id": 3, "name": "Headphones", "price": 100},
]

# Função para publicar eventos no RabbitMQ
def publicar_evento(routing_key, mensagem):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange, exchange_type='direct')
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=json.dumps(mensagem)
    )
    connection.close()

# Endpoint para listar produtos
@app.get("/products")
def get_products():
    return {"products": products}

# Endpoint para criar pedido
@app.post("/pedidos")
def criar_pedido():
    # Simulação de criação de pedido
    pedido = {'order_id': 123, 'status': 'Pedido criado'}
    publicar_evento(pedidos_criados_key, pedido)
    return {"message": "Pedido criado", "pedido": pedido}

# Endpoint para aprovar pagamento
@app.post("/pedidos/{order_id}/aprovar")
def aprovar_pagamento(order_id: int):
    pedido = {'order_id': order_id, 'status': 'Pagamento aprovado'}
    publicar_evento(pagamentos_aprovados_key, pedido)
    return {"message": "Pagamento aprovado", "pedido": pedido}

# Endpoint para recusar pagamento
@app.post("/pedidos/{order_id}/recusar")
def recusar_pagamento(order_id: int):
    pedido = {'order_id': order_id, 'status': 'Pagamento recusado'}
    publicar_evento(pagamentos_recusados_key, pedido)
    publicar_evento(pedidos_excluidos_key, pedido)  # Publica no tópico de pedidos excluídos
    return {"message": "Pagamento recusado", "pedido": pedido}

# Endpoint para enviar pedido
@app.post("/pedidos/{order_id}/enviar")
def enviar_pedido(order_id: int):
    pedido = {'order_id': order_id, 'status': 'Pedido enviado'}
    publicar_evento(pedidos_enviados_key, pedido)
    return {"message": "Pedido enviado", "pedido": pedido}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)