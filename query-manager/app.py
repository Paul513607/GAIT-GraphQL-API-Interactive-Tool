import re
from typing import List
from fastapi import FastAPI, HTTPException
import requests
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from api_data import Api, apis

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

class QueryRequest(BaseModel):
    api_url: str  # The GraphQL API URL
    model: str     # The model to be used (e.g., OpenAI, CustomModel)
    user_input: str  # The user's natural language query

def call_openai_local(api_url: str, user_input: str):
    openai_api_url = f"http://localhost:5000/generate_query?api_url={api_url}&user_input={user_input}"
    
    try:
        response = requests.get(openai_api_url)
        response.raise_for_status() 
        data = response.json()
        raw_query = data["query"]
        cleaned_query = re.sub(r"^```graphql\n|```$", "", raw_query).strip()
        
        return { "query": cleaned_query }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI local API: {e}")

@app.post("/generate_query")
async def generate_graphql_query(request: QueryRequest):
    print(f"Received request with API URL: {request.api_url}")
    print(f"Using model: {request.model}")
    print(f"User query: {request.user_input}")

    if request.model.lower() == "openai":
        try:
            result = call_openai_local(request.api_url, request.user_input)
            print(result)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to call OpenAI API: {e}")
    else:
        return {"message": "Model is not implemented yet"}  

@app.get("/apis", response_model=List[Api])
async def get_apis():
    return apis

