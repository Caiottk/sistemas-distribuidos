from defines import *  # Ensure this contains necessary RabbitMQ configurations
import asyncio
import json
import aio_pika  # Use aio-pika for asynchronous RabbitMQ communication
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

order_queue = asyncio.Queue()

class Notificacao:
    @staticmethod
    async def subscribe_to_topics():
        connection = await aio_pika.connect_robust(host=host)
        channel = await connection.channel()
        exchange = await channel.declare_exchange("e_commerce", aio_pika.ExchangeType.TOPIC)

        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(exchange, routing_key=pedidos_excluidos_key)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    body = message.body.decode('utf-8')
                    order = json.loads(body)
                    await order_queue.put(order) 

    @staticmethod
    async def generate_order_updates():
        while True:
            order = await order_queue.get()
            yield f"data: {json.dumps(order)}\n\n"

@app.get("/notificacao")
async def sse():
    return StreamingResponse(
        Notificacao.generate_order_updates(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(Notificacao.subscribe_to_topics())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)