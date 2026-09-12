import sqlite3
import json
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

DB_NAME = "leaderboard.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

init_db()

def save_score_and_get_top(player_name: str, score: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # ثبت امتیاز جدید
        cursor.execute("INSERT INTO records (player_name, score) VALUES (?, ?)", (player_name, score))
        conn.commit()
        
        # محاسبه رتبه بازیکن در کل دیتابیس
        cursor.execute("SELECT COUNT(*) FROM records WHERE score > ?", (score,))
        rank = cursor.fetchone()[0] + 1
        
        # دریافت ۱۰ نفر برتر تاریخ بازی
        cursor.execute("SELECT player_name, score FROM records ORDER BY score DESC LIMIT 10")
        top_players = [{"name": row[0], "score": row[1]} for row in cursor.fetchall()]
        
        return rank, top_players

@app.get("/")
async def get():
    with open("./index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            event = json.loads(data)
            
            if event.get("action") == "game_over":
                player_name = event.get("player_name", "بازیکن ناشناس").strip()
                if not player_name:
                    player_name = "ناشناس"
                
                final_score = int(event.get("score", 0))
                
                # ذخیره و دریافت جدول رده‌بندی
                rank, top_10 = save_score_and_get_top(player_name, final_score)
                
                await websocket.send_text(json.dumps({
                    "type": "game_over_ack",
                    "final_score": final_score,
                    "player_rank": rank,
                    "leaderboard": top_10
                }, ensure_ascii=False))
                
    except WebSocketDisconnect:
        pass
