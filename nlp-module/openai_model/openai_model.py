import requests
from openai import OpenAI
import os

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.requests import RequestsHTTPTransport
from dotenv import load_dotenv

from common.schema_fetcher import fetch_graphql_schema

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_graphql_query(api_url, user_input):
    """Generate a GraphQL query based on user input."""
    schema = fetch_graphql_schema(api_url)
    schema_text = str(schema)  # Convert schema JSON to string for OpenAI

    prompt = f"""
    Given the following GraphQL schema:
    {schema_text}

    Generate a GraphQL query that matches this user request:
    "{user_input}"
    """

    response = client.chat.completions.create(model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are an expert GraphQL query generator. You are to only show the generated query."},
        {"role": "user", "content": prompt}
    ])

    return response.choices[0].message.content
