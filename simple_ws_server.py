#!/usr/bin/env python3
import asyncio
import websockets
import json
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head><title>WebSocket Test</title></head>
    <body>
        <h1>WebSocket Test</h1>
        <button onclick="test()">Test WebSocket</button>
        <div id="output"></div>
        <script>
            function test() {
                const ws = new WebSocket('ws://localhost:8000/ws/test');
                ws.onopen = () => {
                    document.getElementById('output').innerHTML += '<p>✅ Connected!</p>';
                    ws.send(JSON.stringify({message: 'Hello'}));
                };
                ws.onmessage = (event) => {
                    document.getElementById('output').innerHTML += '<p>📨 Received: ' + event.data + '</p>';
                };
                ws.onerror = (error) => {
                    document.getElementById('output').innerHTML += '<p>❌ Error: ' + error + '</p>';
                };
            }
        </script>
    </body>
    </html>
    """)

@app.websocket("/ws/test")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await websocket.send_text(json.dumps({
                "status": "success",
                "message": f"Echo: {message.get('message', 'No message')}"
            }))
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 