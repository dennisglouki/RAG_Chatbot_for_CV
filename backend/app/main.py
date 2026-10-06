from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from app.chatbot import Bot
from collections import defaultdict
from app.DB_communication import Database, GeoLocator



app = FastAPI(
    title="CV RAG Chatbot",
    description="Chat with Dennis' CV using Gemini and RAG",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://dennisg.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(  max_length=3000)
    history: list[dict] = []


chatbot = Bot()
db = Database()
geo_locator = GeoLocator()


messages_counter = defaultdict(int)


@app.get("/")
def home():
    return {
        "message": "CV RAG chatbot is running"
    }


@app.get("/check/status")
def status():
    return {
        "status": "ok"
    }

@app.get("/health")
def status():
    return {
        "status": "ok"
    }


@app.post("/chat")
async def chat(request_ip: Request, request: ChatRequest):
    message_limit = 8
    client_ip = request_ip.client.host
    messages_counter = db.get_daily_request_count(client_ip)

    if messages_counter >= message_limit:
        results = {}
        return {"answer": "Unfortunately, you've reached the daily 8-question limit. To keep the chatbot free, no further questions are available. Thanks for chatting! 😊", "message_count": messages_counter, 'message_limit': message_limit}
    else:
        results = chatbot.execute_bot(request.message, request.history, k=50)
        answer = results["answer"]
        sources = results["sources"] 
        
        if messages_counter == 2:
            answer = "Wow, you're really curious! 😄 Let's grab a coffee instead of chatting here ☕. Reach out to me at dennisgloukhman@hotmail.de\n\n Back to your question:   " + answer

    meta = results.get('meta', {})
    location = geo_locator.get_location(client_ip)
    db.store_request(
        ip_address=request_ip.client.host,
        question=request.message,
        answer=results.get("answer"),
        model=meta.get('model_version'),
        input_tokens=meta.get('input_tokens'),
        output_tokens=meta.get('output_tokens'),
        total_tokens=meta.get('total_tokens'),
        status= meta.get('status', 'No request'),
        country= location.get('country'),
        city= location.get('city')) 
    
    
    return {"answer": answer, "sources": sources, "message_count": messages_counter, 'message_limit': message_limit  }


