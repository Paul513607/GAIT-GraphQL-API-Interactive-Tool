import requests
from openai import OpenAI
import os

from flask import Flask, Response, request, jsonify
from dotenv import load_dotenv
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.requests import RequestsHTTPTransport
from rdflib import Graph, Namespace, RDF, RDFS, URIRef, Literal

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
        {"role": "system", "content": "You are an expert GraphQL query generator. You are to only show the generated query."},
        {"role": "user", "content": prompt}
    ])

    return response.choices[0].message.content

def convert_schema_to_rdf(schema):
    """Convert GraphQL schema to RDF format."""
    graph = Graph()
    GRAPHQL = Namespace("http://example.org/graphql#")

    graph.bind("graphql", GRAPHQL)

    for gql_type in schema["types"]:
        type_name = gql_type["name"]
        kind = gql_type["kind"]

        type_uri = URIRef(f"http://example.org/graphql#{type_name}")
        graph.add((type_uri, RDF.type, RDFS.Class))
        graph.add((type_uri, RDFS.label, Literal(type_name)))

        if kind == "OBJECT" and "fields" in gql_type:
            for field in gql_type["fields"]:
                field_name = field["name"]
                field_type = field["type"]["name"]

                field_uri = URIRef(f"http://example.org/graphql#{field_name}")
                graph.add((field_uri, RDF.type, RDF.Property))
                graph.add((field_uri, RDFS.label, Literal(field_name)))

                if field_type:
                    field_type_uri = URIRef(f"http://example.org/graphql#{field_type}")
                    graph.add((field_uri, RDFS.range, field_type_uri))
                    graph.add((type_uri, RDFS.subClassOf, field_type_uri))

    return graph.serialize(format="turtle")

@app.route('/generate_query', methods=['GET'])
def generate_query():
    api_url = request.args.get('api_url')
    user_input = request.args.get('user_input')

    if not api_url or not user_input:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        query = generate_graphql_query(api_url, user_input)
        return jsonify({"query": query})
        # return jsonify({"query": "```graphql\nquery {\n  countries(filter: {continent: {eq: \"EU\"}}) {\n    code\n    name\n    capital\n    awsRegion\n    currency\n    emoji\n    languages {\n      code\n      name\n      native\n    }\n    states {\n      code\n      name\n    }\n  }\n}\n```"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate_rdf', methods=['GET'])
def generate_rdf():
    api_url = request.args.get('api_url')

    if not api_url:
        return jsonify({"error": "Missing required parameter: api_url"}), 400

    try:
        schema = fetch_graphql_schema(api_url)
        rdf_data = convert_schema_to_rdf(schema)
        return Response(rdf_data, mimetype="text/turtle")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
