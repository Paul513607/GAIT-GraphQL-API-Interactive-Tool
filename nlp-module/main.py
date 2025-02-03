from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from flask_restx import Api, Resource, fields
from rdflib import Graph, Namespace, RDF, RDFS, URIRef, Literal
from rdflib.plugins.sparql import prepareQuery

from common.schema_fetcher import fetch_graphql_schema
from openai_model import openai_model
from nlp_custom_model import nlp_main
from rdf.rdf_processor import convert_schema_to_rdf

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

api = Api(app, title="GAIT API", description="A GraphQL Query Generator API", version="1.0")  # Swagger UI

ns = api.namespace("apis", description="Query Endpoints")

GRAPHQL = Namespace("http://example.org/graphql#")

query_model = api.model(
    "QueryInput",
    {
        "api_url": fields.String(required=True, description="GraphQL API URL"),
        "user_input": fields.String(required=True, description="User query input"),
        "model": fields.String(required=True, description="NLP Model ('openai' or 'custom')"),
    },
)

query_response_model = api.model(
    "QueryResponse",
    {
        "query": fields.String(description="Generated GraphQL query"),
        "error": fields.String(description="Error message (if any)"),
    },
)

last_api_url = None

@ns.route('/generate_query')
class GenerateQuery(Resource):
    @api.expect(query_model)
    @api.marshal_with(query_response_model)
    def get(self):
        global last_api_url
        api_url = request.args.get('api_url')
        user_input = request.args.get('user_input')
        model = request.args.get('model').lower()

        if not api_url or not user_input or not model:
            return {"error": "Missing required parameters"}, 400

        last_api_url = api_url
        try:
            if model == "openai":
                query = openai_model.generate_graphql_query(api_url, user_input)
            elif model == "custom":
                query = nlp_main.get_graphql_query(api_url, user_input)
                if not query:
                    return {"error": "Resource not recognized. Please try again."}, 400
            else:
                return {"error": "Invalid model type"}, 400

            return {"query": query}
        except Exception as e:
            return {"error": str(e)}, 500

@ns.route('/generate_rdf')
class GenerateRDF(Resource):
    @api.doc(params={"api_url": "GraphQL API URL"})
    def get(self):
        global last_api_url
        api_url = request.args.get('api_url')

        if not api_url:
            return {"error": "Missing required parameter: api_url"}, 400

        last_api_url = api_url
        try:
            _, schema = fetch_graphql_schema(api_url)
            rdf_data = convert_schema_to_rdf(schema)
            return Response(rdf_data, mimetype="text/turtle")
        except Exception as e:
            return {"error": str(e)}, 500

@ns.route('/entities')
class Entities(Resource):
    @api.doc(params={"api_url": "GraphQL API URL"})
    def get(self):
        global last_api_url
        api_url = request.args.get('api_url')
        last_api_url = api_url
        base_url = request.host_url.rstrip("/")

        if not api_url:
            api_url = last_api_url
        else:
            last_api_url = api_url

        try:
            _, schema = fetch_graphql_schema(api_url)
            graph = convert_schema_to_rdf(schema)

            query = prepareQuery(
                """
                SELECT ?entity WHERE {
                    ?entity a rdfs:Class .
                }
                """
            )

            entities = [
                {
                    "uri": f"{base_url}/apis/entities/{str(row.entity).split('#')[-1]}",
                }
                for row in graph.query(query)
            ]
            return {"entities": entities}
        except Exception as e:
            return {"error": str(e)}, 500

@ns.route('/entities/<string:entity_name>')
class Fields(Resource):
    @api.doc(params={"api_url": "GraphQL API URL"})
    def get(self, entity_name):
        global last_api_url
        api_url = request.args.get('api_url')
        base_url = request.host_url.rstrip("/")

        if not api_url:
            api_url = last_api_url
        else:
            last_api_url = api_url

        try:
            _, schema = fetch_graphql_schema(api_url)
            for gql_type in schema["types"]:
                if gql_type["name"] == entity_name and gql_type["kind"] == "OBJECT":
                    fields = [f"uri: {base_url}/apis/entities/{entity_name}/{field['name']}" for field in gql_type.get("fields", [])]
                    return {"entity": entity_name, "fields": fields}
            return {"error": f"Entity '{entity_name}' not found"}, 404
        except Exception as e:
            return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)