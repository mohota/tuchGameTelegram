from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

# ذخیره بالاترین امتیازات بازیکنان (در نسخه واقعی باید در دیتابیس مثل PostgreSQL ذخیره شود)
high_scores = {}

@app.get("/")
async def get():
    with open("./index2.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # برای تست، یک آیدی تصادفی یا ثابت در نظر می‌گیریم
    player_id = f"player_{id(websocket)}" 
    
    try:
        while True:
            data = await websocket.receive_text()
            event = json.loads(data)
            
            if event["action"] == "game_over":
                final_score = event["score"]
                current_high_score = high_scores.get(player_id, 0)
                
                # آپدیت رکورد اگر امتیاز جدید بیشتر باشد
                is_new_record = False
                if final_score > current_high_score:
                    high_scores[player_id] = final_score
                    is_new_record = True
                
                # ارسال نتیجه و رکورد فعلی به کلاینت
                await websocket.send_text(json.dumps({
                    "type": "result",
                    "final_score": final_score,
                    "high_score": high_scores[player_id],
                    "is_new_record": is_new_record
                }))
                
    except WebSocketDisconnect:
        pass
