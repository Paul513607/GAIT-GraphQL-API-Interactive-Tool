import requests
from openai import OpenAI
import os

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.requests import RequestsHTTPTransport

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

app = Flask(__name__)


def fetch_graphql_schema(api_url):
    transport = RequestsHTTPTransport(url=api_url)
    client = Client(transport=transport, fetch_schema_from_transport=True)

    """
    Fetch the GraphQL schema using introspection.
    """
    query = gql("""
    query IntrospectionQuery {
      __schema {
        queryType { name }
        types {
          ...FullType
        }
      }
    }
    fragment FullType on __Type {
      kind
      name
      fields(includeDeprecated: true) {
        name
        args {
          name
          type {
            ...TypeRef
          }
        }
        type {
          ...TypeRef
        }
      }
      inputFields {
        name
        type { ...TypeRef }
      }
    }
    fragment TypeRef on __Type {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
        }
      }
    }
    """)
    response = client.execute(query)
    return response["__schema"]

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
        {"role": "system", "content": "You are an expert GraphQL query generator."},
        {"role": "user", "content": prompt}
    ])

    return response.choices[0].message.content


@app.route('/generate_query', methods=['GET'])
def generate_query():
    api_url = request.args.get('api_url')
    user_input = request.args.get('user_input')

    if not api_url or not user_input:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        query = generate_graphql_query(api_url, user_input)
        return jsonify({"query": query})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
