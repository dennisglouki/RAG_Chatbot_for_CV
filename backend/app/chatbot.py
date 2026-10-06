import faiss
import json
from google import genai
import pathlib
from app.prompt import SYSTEM_PROMPT
import numpy as np
from pydantic import BaseModel

class ChatResponse(BaseModel):
    answer: str
    relevant_contexts: list[int]

class Bot:
    def __init__(self):
        self.client = genai.Client()

        data_folder = pathlib.Path(__file__).resolve().parent.parent / "data"
        self.index = faiss.read_index(
            str(data_folder / "files.index")
        )
        with open(data_folder / "chunks.json") as f:
            self.chunks = json.load(f)
        

    def prepare_query(self, query):
        return f"task: search result | query: {query}"


    def embed_query(self, query):
        prepared_query = self.prepare_query(query)
        result = self.client.models.embed_content(
            model='gemini-embedding-2',
            contents=prepared_query,
        )
        embedding = result.embeddings[0].values

        return np.asarray(
            embedding,
            dtype=np.float32,
        )

    def search(self,query, k=7, threshold= .535):
        query_embedding = self.embed_query(query)

        scores, indices = self.index.search(
            np.array([query_embedding]),
            k
        )

        return [
            self.chunks[i]
            #for i in indices[scores>threshold]
            for i in indices[0]
        ]

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


    def execute_bot(self, question, history,k =7):
        context = self.search(question, k=k)
        prompt = self.create_prompt(question, context, history)
        response = self.client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "response_mime_type": "application/json",
                "response_schema": ChatResponse,
            },
        )
        
        sources = [
        {
            "source": item["source"],
            "page": item["page_nr"],
            "url": item["url"],
            "lines": item['lines'] 
            #"text": item['text'],
        }
        for i, item in enumerate(context)
        if i + 1 in response.parsed.relevant_contexts
    ]

        finish_reason = None
        if response.candidates:
            finish_reason = response.candidates[0].finish_reason.name
        response_meta= {
            "model":response.model_version,
            "input_tokens":response.usage_metadata.prompt_token_count,
            "output_tokens":response.usage_metadata.candidates_token_count,
            "total_tokens":response.usage_metadata.total_token_count,
            "response_id":response.response_id,
            "status": finish_reason}

        return {
            "answer": response.parsed.answer,
            "sources": sources,
            "meta": response_meta
        }



