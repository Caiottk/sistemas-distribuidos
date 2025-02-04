from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
import asyncio
import json
from fastapi.middleware.cors import CORSMiddleware  
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from this origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Simulated function to generate order updates
async def generate_order_updates():
    order_id = 1
    flag = False
    status = "Processing"
    while True:
        # Simulate an order status update
        if flag:
            flag = not flag
            status = "Completed"
        else:
            flag = not flag
            status = "Processing"

        order = {
            "order_id": order_id,
            "status": status
        }
        yield f"data: {json.dumps(order)}\n\n"
        await asyncio.sleep(1)  # Simulate a delay between updates

@app.get("/notificacao")
async def sse():
    # Return a StreamingResponse for SSE
    return StreamingResponse(
        generate_order_updates(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)