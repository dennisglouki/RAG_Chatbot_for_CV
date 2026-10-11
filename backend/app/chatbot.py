from google import genai
from app.prompt import SYSTEM_PROMPT
import numpy as np
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import os
import json
import re

import time  


COLLECTION_NAME = os.getenv("COLLECTION_NAME", "MoreThan1Page")

class ChatResponse(BaseModel):
    answer: str
    relevant_contexts: list[int]

class Bot:
    def __init__(self):
        self.client = genai.Client()
        self.client_qd = QdrantClient(
            url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"]
        )
     
        

    def prepare_query(self, query):
        return f"task: search result | query: {query}"


    def embed_query(self, query):
        prepared_query = self.prepare_query(query)
        result = self.client.models.embed_content(
            model='gemini-embedding-2',
            contents=prepared_query,
        )
        embedding = result.embeddings[0].values

        embedding_meta= {
                    "model":'gemini-embedding-2',
                    "total_tokens":None,
                    "type": 'embedding'
                    }
        
       

        return {'embedding': np.asarray(
            embedding,
            dtype=np.float32,
        ), 'meta': embedding_meta}

    def search(self,query, k=50 , client_id = None):
    
        results = self.client_qd.query_points(
            collection_name= COLLECTION_NAME,
            query=query,
            with_payload=True,
            score_threshold=0.5,  
            query_filter= Filter(
                    must=[  # These conditions are required for search results
                        FieldCondition(
                            key='client_user', match=MatchValue(value=client_id)) ] 
                        ),
            limit=k )
        
        chunks = [point.payload for point in results.points]
        return chunks

    def create_prompt(self, question,context, history):
        cont = ''
        for num, i in enumerate(context):
            cont += f'''Context {num+1}
            Source file: {i['source']}
            Page in Source: {i['page_nr']}
            Text of context: {i['text']}\n'''


        conversation = ''

        for message in history:
            conversation += f"{message['role']}: {message['content']}\n"

        return f"""
    CONTEXT:
    {cont}

    PREVIOUS CONVERSATION:
    {conversation}

    CURRENT USER QUESTION:
    {question}
    """

    def extract_streamed_answer(self, response_text):
        """Extract the answer field from partially generated JSON."""
        match = re.search(r'"answer"\s*:\s*"', response_text)

        if not match:
            return ""

        answer_start = match.end()
        answer_part = response_text[answer_start:]

        # Find the end of the JSON string, ignoring escaped quotes.
        i = 0
        while i < len(answer_part):
            if answer_part[i] == "\\":
                i += 2
                continue

            if answer_part[i] == '"':
                answer_part = answer_part[:i]
                break

            i += 1

        try:
            return json.loads('"' + answer_part + '"')
        except json.JSONDecodeError:
            return ""


    def execute_bot(self, question, history,client_id = 'DennisCV', k =7):    
        
        start_time = time.perf_counter()
        embedded_query = self.embed_query(question)
        print( 'embed_query:', time.perf_counter()-start_time)

        start_time = time.perf_counter()
        context = self.search(embedded_query['embedding'], k=k, client_id=client_id)
        print( 'search:', time.perf_counter()-start_time)

        start_time = time.perf_counter()
        prompt = self.create_prompt(question, context, history)
        print( 'create prompt:', time.perf_counter()-start_time)

        start_time = time.perf_counter()

        # response = self.client.models.generate_content(
        #     model="gemini-3.8-flash",
        #     contents=prompt,
        #     config={
        #         "system_instruction": SYSTEM_PROMPT,
        #         "response_mime_type": "application/json",
        #         "response_schema": ChatResponse,
        #         "thinking_config": {
        #         "thinking_level": "low"},
        #     },
        # )

        response_text = ""
        last_chunk = None

        for chunk in self.client.models.generate_content_stream(
            model="gemini-3.8-flash",
            contents=prompt,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "response_mime_type": "application/json",
                "response_schema": ChatResponse,
                "thinking_config": {
                    "thinking_level": "low"
                },
            },
        ):
            if chunk.text:
                response_text += chunk.text
                print(chunk.text, end="", flush=True)

            last_chunk = chunk
        print("STREAMED JSON:", response_text)
        parsed_response = ChatResponse.model_validate_json(response_text)
        print( 'gemini call :', time.perf_counter()-start_time)
        
        start_time = time.perf_counter()
        if parsed_response is None:
            print("Gemini returned no parsed response")
            print("Finish reason:", response.candidates[0].finish_reason
                if response.candidates else None)
            print("Raw response:", response.text)

            raise ValueError("LLM returned no valid ChatResponse")

        
        sources = [
        {
            "source": item["source"],
            "page": item["page_nr"],
            "url": item["url"],
            "lines": item['lines'] 
            #"text": item['text'],
        }
        for i, item in enumerate(context)
        if i + 1 in parsed_response.relevant_contexts
    ]
       
        finish_reason = None
        if last_chunk and last_chunk.candidates:
            reason = last_chunk.candidates[0].finish_reason
            finish_reason = reason.name if reason else None

        usage = getattr(last_chunk, "usage_metadata", None)

        response_meta = {
            "model": getattr(last_chunk, "model_version", None),
            "input_tokens": getattr(usage, "prompt_token_count", None),
            "output_tokens": getattr(usage, "candidates_token_count", None),
            "total_tokens": getattr(usage, "total_token_count", None),
            "response_id": getattr(last_chunk, "response_id", None),
            "status": finish_reason,
            "type": "message"
        }

        print("returning data:", time.perf_counter() - start_time)
        return {
            "answer": parsed_response.answer,
            "sources": sources,
            "meta": {
                "response": response_meta,
                "embedding": embedded_query["meta"]
            }
        }



    def execute_bot_stream(self, question, history, client_id="DennisCV", k=7):
        embedded = self.embed_query(question)
        context = self.search(embedded["embedding"], k=k, client_id=client_id)
        prompt = self.create_prompt(question, context, history)

        response_text, sent_answer, last_chunk = "", "", None

        for chunk in self.client.models.generate_content_stream(
            model="gemini-3.8-flash",
            contents=prompt,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "response_mime_type": "application/json",
                "response_schema": ChatResponse,
                "thinking_config": {"thinking_level": "low"},
            },
        ):
            last_chunk = chunk
            if not chunk.text:
                continue

            response_text += chunk.text
            match = re.search(r'"answer"\s*:\s*"', response_text)
            if not match:
                continue

            raw = response_text[match.end():]
            answer = ""
            for i, char in enumerate(raw):
                if char == "\\":
                    continue
                if char == '"':
                    break
            else:
                i = len(raw)

            try:
                answer = json.loads('"' + raw[:i] + '"')
            except json.JSONDecodeError:
                continue

            if answer.startswith(sent_answer):
                new_text = answer[len(sent_answer):]
                if new_text:
                    sent_answer = answer
                    yield {"type": "token", "text": new_text}

        parsed = ChatResponse.model_validate_json(response_text)
        sources = [
            {"source": c["source"], "page": c["page_nr"],
            "url": c["url"], "lines": c["lines"]}
            for i, c in enumerate(context)
            if i + 1 in parsed.relevant_contexts
        ]

        usage = getattr(last_chunk, "usage_metadata", None)
        reason = last_chunk.candidates[0].finish_reason if last_chunk and last_chunk.candidates else None

        yield {
            "type": "done",
            "answer": parsed.answer,
            "sources": sources,
            "meta": {
                "response": {
                    "model": getattr(last_chunk, "model_version", None),
                    "input_tokens": getattr(usage, "prompt_token_count", None),
                    "output_tokens": getattr(usage, "candidates_token_count", None),
                    "total_tokens": getattr(usage, "total_token_count", None),
                    "response_id": getattr(last_chunk, "response_id", None),
                    "status": reason.name if reason else None,
                    "type": "message",
                },
                "embedding": embedded["meta"],
            },
        }
