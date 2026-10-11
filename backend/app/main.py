from uuid import UUID
import time
import json


from fastapi import FastAPI, Request, BackgroundTasks
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.chatbot import Bot
from app.DB_communication import Database



app = FastAPI(
    title="CV RAG Chatbot",
    description="Chat with Dennis' CV using Gemini and RAG",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://dennisg.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(max_length=10000)
    session_id: UUID | None = None


chatbot = Bot()
db = Database()


@app.get("/")
def home():
    return {"message": "CV RAG chatbot is running"}


@app.get("/check/status")
def status():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat/{slug}")
async def chat(
    slug: str,
    request_ip: Request,
    request: ChatRequest,
    background_tasks: BackgroundTasks,
):
    message_limit = 8
    client_ip = request_ip.client.host

    # 1. Resolve the public chatbot slug to its internal customer UUID
    customer_id = db.lookup_id(slug)
    # 2. Check the daily question limit

    request_count = db.get_daily_request_count(client_ip)

    if request_count >= message_limit:
        def limit_stream():
            message = (
                "Unfortunately, you've reached the daily 8-question limit. "
                "To keep the chatbot free, no further questions are available. "
                "Thanks for chatting! 😊"
            )

            yield f"data: {json.dumps({'type': 'chunk', 'text': message})}\n\n"

            yield f"data: {json.dumps({
                'type': 'done',
                'answer': message,
                'message_count': request_count,
                'message_limit': message_limit,
                'session_id': str(request.session_id) if request.session_id else None,
                'sources': []
            })}\n\n"

        return StreamingResponse(
            limit_stream(),
            media_type="text/event-stream",
            )

    # 3. Validate the existing session or create a new one
    session_id = (
        str(request.session_id)
        if request.session_id is not None
        else None
    )
    if (
        session_id is None
        or not db.validate_session(session_id, customer_id)
    ):
        location = db.get_location(client_ip)

        
        session_id = db.create_session(
            customer_id=customer_id,
            ip_address=client_ip,
            country=location.get("country"),
            city=location.get("city"),
        )

    # 4. Load conversation history from PostgreSQL
    history = db.get_session_history(session_id)

    # 5. Generate the answer

    # results = chatbot.execute_bot(
    #     request.message,
    #     history,
    #     k=50,
    #     client_id=customer_id,
    # )
    
    def generate():
        answer = None
        meta = {}
        embedding_meta = {}
        start_time = time.perf_counter() 
        try:
            for event in chatbot.execute_bot_stream(
                request.message,
                history,
                k=50,
                client_id=customer_id,
            ):
                if event["type"] == "done":
                    answer = event.get("answer")
                    meta = event.get("meta", {}).get("response", {})
                    embedding_meta = event.get("meta", {}).get("embedding", {})
                    embedding_meta['total_tokens'] = len(request.message.split(' '))+8

                    # Send session information to the frontend
                    event["session_id"] = session_id
                    event["message_count"] = request_count + 1
                    event["message_limit"] = message_limit
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()

            yield f"data: {json.dumps({
                'type': 'error',
                'message': 'Response generation failed'
            })}\n\n"
  
        # Keep your existing logging code here
        finally:
            if answer is not None:

                background_tasks.add_task(
                    db.log_request,
                    session_id=session_id,
                    question=request.message,
                    answer=None,
                    meta=embedding_meta,
                    type="embedding",
                )
                background_tasks.add_task(
                    db.log_request,
                    session_id=session_id,
                    question=request.message,
                    answer=answer,
                    meta=meta,
                    duration_s=time.perf_counter() - start_time,
                    type="message",
                )
    return StreamingResponse(
    generate(),
    media_type="text/event-stream",
)

    # duration_s = time.perf_counter() - start_time

    # print( 'geminin execute :', duration_s)

    # answer = results["answer"]
    # sources = results["sources"]
    # meta = results.get("meta", {}).get('response', {})
    # embedding_meta = results.get("meta", {}).get('embedding', {})
    # embedding_meta['total_count'] = len(request.message.split())+6 

    # # Preserve your existing personalized message
    # if request_count == 2:
    #     answer = (
    #         "Wow, you're really curious! 😄 Let's grab a coffee instead "
    #         "of chatting here ☕. Reach out to me at "
    #         "dennisgloukhman@hotmail.de\n\n"
    #         "Back to your question: " + answer
    #     )

    # start_time = time.perf_counter()
    # # Embedding logging
    # background_tasks.add_task(
    #     db.log_request,
    #     session_id=session_id,
    #     question=request.message,
    #     answer=None,
    #     meta=embedding_meta,
    #     type="embedding",
    # )

    # # LLM response logging
    # background_tasks.add_task(
    #     db.log_request,
    #     session_id=session_id,
    #     question=request.message,
    #     answer=answer,
    #     meta=meta,
    #     duration_s=duration_s,
    #     type="message",
    # )

    # print( 'background_logging :', time.perf_counter()-start_time)
    # print( 'total time:', time.perf_counter()-start_total)

    # # 7. Return the session ID for the frontend to reuse
    # return {
    #     "answer": answer,
    #     "sources": sources,
    #     "session_id": session_id,
    #     "message_count": request_count + 1,
    #     "message_limit": message_limit,
    # }