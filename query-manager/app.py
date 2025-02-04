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
    api_url: str 
    model: str     
    user_input: str 

NLP_MODULE_URL = "http://127.0.0.1:5000/apis"

def call_nlp_module(api_url: str, user_input: str, model: str):
    api_url = f"{NLP_MODULE_URL}/generate_query?api_url={api_url}&model={model}&user_input={user_input}"
    
    try:
        response = requests.get(api_url)
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

    try:
        result = call_nlp_module(request.api_url, request.user_input, request.model)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to call OpenAI API: {e}")

@app.get("/apis", response_model=List[Api])
async def get_apis():
    return apis

@app.get("/entities")
def fetch_country_entity(api_url: str):
    api_url = f"{NLP_MODULE_URL}/entities?api_url={api_url}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        if "entities" in data and isinstance(data["entities"], list):
            return data["entities"]
        else:
            raise HTTPException(status_code=400, detail="Invalid response format: 'entities' key not found")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching entities: {str(e)}")

@app.get("/entities/{entity}")
def fetch_entities(entity: str):
    api_url = f"{NLP_MODULE_URL}/entities/{entity}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        if "fields" in data and isinstance(data["fields"], list):
            return data["fields"]
        else:
            return []
    except requests.RequestException as e:
        return []



