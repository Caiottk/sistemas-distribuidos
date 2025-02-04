from fastapi import FastAPI, HTTPException, Request
import pika
import json
import uuid
import threading
from defines import *
import asyncio
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware  

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
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange, exchange_type="topic")
        channel.basic_publish(
            exchange=exchange,
            routing_key=get_estoques_key,
            body=json.dumps({"get_estoque": True, "correlation_id": correlation_id}),
        )
        connection.close()

    @staticmethod
    def publish_pedidos_criados(pedido):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange, exchange_type="topic")
        channel.basic_publish(
            exchange=exchange,
            routing_key=pedidos_criados_key,
            body=json.dumps(pedido),
        )
        connection.close()

    def on_pagamento_recusado(ch, method, properties, body):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type="topic")

            # Parse the incoming message
            message = json.loads(body)

            # Publish the response to the estoques_key routing key
            channel.basic_publish(
                exchange=exchange,
                routing_key=pedidos_excluidos_key,
                body=json.dumps(message),
            )
            connection.close()

            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(message)
            print("Pedido Excluido com Sucesso")
            return True
        except Exception as e:
            print(f"Erro ao Excluir Pedido :\n{e}")
            return False
    
    def on_pedidos_enviados(ch, method, properties, body):
        message = json.loads(body)
        print(message)

    # Function to consume messages from RabbitMQ
    @staticmethod
    def consume_from_rabbitmq():
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange, exchange_type="topic")

        # Declare a temporary queue
        result = channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue

        # Bind the queue to the exchange with the correct routing key
        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=estoques_key)

        def callback(ch, method, properties, body):
            message = json.loads(body)
            correlation_id = message.get("correlation_id")
            if correlation_id in Principal.responses:
                Principal.responses[correlation_id] = message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=queue_name, on_message_callback=callback)

        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pagamentos_recusados_key)
        channel.basic_consume(queue=queue_name, on_message_callback=Principal.on_pagamento_recusado)

        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=pedidos_enviados_key)
        channel.basic_consume(queue=queue_name, on_message_callback=Principal.on_pedidos_enviados)

        print("Waiting for messages on estoques_key...")
        channel.start_consuming()

# Start the RabbitMQ consumer in a separate thread
threading.Thread(target=Principal.consume_from_rabbitmq, daemon=True).start()

# FastAPI endpoint
@app.get("/products")
async def get_products():
    correlation_id = str(uuid.uuid4())
    Principal.responses[correlation_id] = None

    # Send message to get_estoques_key
    Principal.publish_get_estoque(correlation_id)

    # Wait for response from estoques_key
    while Principal.responses[correlation_id] is None:
        pass

    response = Principal.responses.pop(correlation_id)
    print(response['produtos'])
    return {"products": response['produtos']}

# FastAPI endpoint
@app.get("/orders")
async def get_orders():
    order_list = []
    for correlation_id,order in Principal.orders.items():
        order["order_id"] = correlation_id
        order_list.append(order)
    return order_list

update_queue = asyncio.Queue()

# Checkout endpoint
@app.post("/checkout")
async def checkout(request: Request):
    try:
        # Parse the JSON payload
        order = await request.json()

        # Validate the required fields
        if not all(key in order for key in ["name", "address", "card", "cart"]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Process the order (e.g., save to database, send to RabbitMQ, etc.)
        print("Received order:", order)
        correlation_id = str(uuid.uuid4())

        Principal.publish_pedidos_criados({"correlation_id":correlation_id,"status":"Aguardando Pagamento","order":order})
        Principal.orders[correlation_id] = order

        # For now, just return a success message
        return {"message": "Order placed successfully", "order": order}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# SSE endpoint to notify product updates
@app.get("/stream-products")
async def stream_products():
    async def event_generator():
        while True:
            product_data = await update_queue.get()  # Wait for an update
            yield f"data: {json.dumps(product_data)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Route to update products (triggers SSE event)
@app.post("/update-products")
async def update_products(new_products: list[dict]):
    global products
    products = new_products
    await update_queue.put({"products": products})  # Notify SSE
    return {"message": "Product list updated"}


@app.post("/payment")
async def payment(request: Request):
    try:
        # Parse the JSON payload
        order = await request.json()
        print(order)
        try:
            int(order["card"])
            return {"Aproved":True}
        except:
            return {"Aproved":False}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)