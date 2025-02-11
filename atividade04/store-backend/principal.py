from fastapi import FastAPI, HTTPException, Request
import pika
import json
import uuid
import threading
from defines import *
import asyncio
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configuração básica do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('principal.log'),  # Salva logs em um arquivo
        logging.StreamHandler()  # Exibe logs no console
    ]
)

app = FastAPI()
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from this origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Dictionary to store responses
class Principal:
    responses = {}
    orders = {}

    # Function to send a message to RabbitMQ
    @staticmethod
    def publish_get_estoque(correlation_id):
        try:
            logging.info(f"Publicando solicitação de estoque com correlation_id: {correlation_id}")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")
            channel.basic_publish(
                exchange=exchange,
                routing_key=get_estoques_key,
                body=json.dumps({"get_estoque": True, "correlation_id": correlation_id}),
            )
            connection.close()
            logging.info("Solicitação de estoque publicada com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao publicar solicitação de estoque: {e}")

    @staticmethod
    def publish_pedidos_criados(pedido):
        try:
            logging.info(f"Publicando pedido criado: {pedido}")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")
            channel.basic_publish(
                exchange=exchange,
                routing_key=pedidos_criados_key,
                body=json.dumps(pedido),
            )
            connection.close()
            logging.info("Pedido criado publicado com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao publicar pedido criado: {e}")

    @staticmethod
    def on_pagamento_recusado(ch, method, properties, body):
        try:
            logging.info("Processando pedido recusado...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")

            # Parse the incoming message
            message = json.loads(body)
            logging.info(f"Mensagem recebida: {message}")

            # Publish the response to the estoques_key routing key
            channel.basic_publish(
                exchange=exchange,
                routing_key=pedidos_excluidos_key,
                body=json.dumps(message),
            )
            connection.close()

            ch.basic_ack(delivery_tag=method.delivery_tag)
            logging.info("Pedido excluído com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao excluir pedido: {e}")

    @staticmethod
    def on_pedidos_enviados(ch, method, properties, body):
        try:
            message = json.loads(body)
            logging.info(f"Pedido enviado recebido: {message}")
        except Exception as e:
            logging.error(f"Erro ao processar pedido enviado: {e}")

    # Function to consume messages from RabbitMQ
    @staticmethod
    def consume_from_rabbitmq():
        try:
            logging.info("Conectando ao RabbitMQ e iniciando consumo de mensagens...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")

            # Declare a temporary queue
            result = channel.queue_declare(queue="", exclusive=True)
            queue_name = result.method.queue

            # Bind the queue to the exchange with the correct routing key
            channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=estoques_key)

            def callback(ch, method, properties, body):
                try:
                    message = json.loads(body)
                    correlation_id = message.get("correlation_id")
                    if correlation_id in Principal.responses:
                        Principal.responses[correlation_id] = message
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    logging.info(f"Mensagem recebida e processada: {message}")
                except Exception as e:
                    logging.error(f"Erro ao processar mensagem do RabbitMQ: {e}")

            channel.basic_consume(queue=queue_name, on_message_callback=callback)

            channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pagamentos_recusados_key)
            channel.basic_consume(queue=queue_name, on_message_callback=Principal.on_pagamento_recusado)

            channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_enviados_key)
            channel.basic_consume(queue=queue_name, on_message_callback=Principal.on_pedidos_enviados)

            logging.info("Aguardando mensagens...")
            channel.start_consuming()
        except Exception as e:
            logging.error(f"Erro ao consumir mensagens do RabbitMQ: {e}")

# Start the RabbitMQ consumer in a separate thread
threading.Thread(target=Principal.consume_from_rabbitmq, daemon=True).start()

# FastAPI endpoint
@app.get("/products")
async def get_products():
    correlation_id = str(uuid.uuid4())
    Principal.responses[correlation_id] = None

    # Send message to get_estoques_key
    Principal.publish_get_estoque(correlation_id)

    # Wait for response from estoques_key with a timeout
    timeout = 30  # Timeout in seconds
    start_time = asyncio.get_event_loop().time()
    while Principal.responses[correlation_id] is None:
        await asyncio.sleep(0.1)  # Libera o event loop
        if asyncio.get_event_loop().time() - start_time > timeout:
            logging.error("Timeout ao aguardar resposta do RabbitMQ.")
            raise HTTPException(status_code=504, detail="Timeout waiting for response from RabbitMQ")

    response = Principal.responses.pop(correlation_id)
    logging.info(f"Retornando lista de produtos: {response['produtos']}")
    return {"products": response['produtos']}

# FastAPI endpoint
@app.get("/orders")
async def get_orders():
    order_list = []
    for correlation_id, order in Principal.orders.items():
        order["order_id"] = correlation_id
        order_list.append(order)
    logging.info(f"Retornando lista de pedidos: {order_list}")
    return order_list

update_queue = asyncio.Queue()

# Checkout endpoint
@app.post("/checkout")
async def checkout(request: Request):
    try:
        # Parse the JSON payload
        order = await request.json()
        logging.info(f"Recebido pedido de checkout: {order}")

        # Validate the required fields
        if not all(key in order for key in ["name", "address", "card", "cart"]):
            logging.error("Campos obrigatórios ausentes no pedido.")
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Process the order (e.g., save to database, send to RabbitMQ, etc.)
        correlation_id = str(uuid.uuid4())
        Principal.publish_pedidos_criados({"correlation_id": correlation_id, "status": "Aguardando Pagamento", "order": order})
        Principal.orders[correlation_id] = order

        logging.info(f"Pedido criado com sucesso: {order}")
        return {"message": "Order placed successfully", "order": order}
    except json.JSONDecodeError:
        logging.error("Erro ao decodificar JSON no checkout.")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logging.error(f"Erro no checkout: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# SSE endpoint to notify product updates
@app.get("/stream-products")
async def stream_products():
    async def event_generator():
        while True:
            product_data = await update_queue.get()  # Wait for an update
            logging.info(f"Enviando atualização de produtos via SSE: {product_data}")
            yield f"data: {json.dumps(product_data)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Route to update products (triggers SSE event)
@app.post("/update-products")
async def update_products(new_products: list[dict]):
    global products
    products = new_products
    await update_queue.put({"products": products})  # Notify SSE
    logging.info(f"Lista de produtos atualizada: {products}")
    return {"message": "Product list updated"}

@app.post("/payment")
async def payment(request: Request):
    try:
        # Parse the JSON payload
        order = await request.json()
        logging.info(f"Processando pagamento para o pedido: {order}")

        try:
            int(order["card"])
            logging.info("Pagamento aprovado.")
            return {"Aproved": True}
        except:
            logging.info("Pagamento recusado.")
            return {"Aproved": False}
    except json.JSONDecodeError:
        logging.error("Erro ao decodificar JSON no pagamento.")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logging.error(f"Erro no pagamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the FastAPI app
if __name__ == "__main__":
    logging.info("Iniciando servidor FastAPI...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)