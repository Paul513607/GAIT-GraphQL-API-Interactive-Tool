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

# Namespace for GraphQL RDF
GRAPHQL = Namespace("http://example.org/graphql#")

# Define models for Swagger documentation
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

# Endpoint to generate a GraphQL query
@ns.route('/generate_query')
class GenerateQuery(Resource):
    @api.expect(query_model)
    @api.marshal_with(query_response_model)
    def get(self):
        """ Generate a GraphQL query from user input """
        api_url = request.args.get('api_url')
        user_input = request.args.get('user_input')
        model = request.args.get('model')

        if not api_url or not user_input or not model:
            return {"error": "Missing required parameters"}, 400

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

# Endpoint to generate RDF data from a GraphQL schema
@ns.route('/generate_rdf')
class GenerateRDF(Resource):
    @api.doc(params={"api_url": "GraphQL API URL"})
    def get(self):
        """ Generate RDF data from GraphQL Schema """
        api_url = request.args.get('api_url')

        if not api_url:
            return {"error": "Missing required parameter: api_url"}, 400

        try:
            _, schema = fetch_graphql_schema(api_url)
            rdf_data = convert_schema_to_rdf(schema)
            return Response(rdf_data, mimetype="text/turtle")
        except Exception as e:
            return {"error": str(e)}, 500

# Endpoint to list all entities (types) in the schema as URIs
@ns.route('/entities')
class Entities(Resource):
    @api.doc(params={"api_url": "GraphQL API URL"})
    def get(self):
        """ List all entities (types) in the schema as URIs with links to fields """
        api_url = request.args.get('api_url')

        if not api_url:
            return {"error": "Missing required parameter: api_url"}, 400

        try:
            _, schema = fetch_graphql_schema(api_url)
            graph = convert_schema_to_rdf(schema)

            # SPARQL query to find all entities (classes)
            query = prepareQuery(
                """
                SELECT ?entity WHERE {
                    ?entity a rdfs:Class .
                }
                """
            )

            entities = [
                {
                    "uri": f"http://localhost:5000/apis/entities/{str(row.entity).split('#')[-1]}?api_url={api_url}",
                }
                for row in graph.query(query)
            ]
            return {"entities": entities}
        except Exception as e:
            return {"error": str(e)}, 500

# Endpoint to list all fields for a specific entity
@ns.route('/entities/<path:entity_uri>')
class Fields(Resource):
    @api.doc(params={"api_url": "GraphQL API URL"})
    def get(self, entity_uri):
        """ List all fields for a specific entity """
        api_url = request.args.get('api_url')

        if not api_url:
            return {"error": "Missing required parameter: api_url"}, 400

        try:
            _, schema = fetch_graphql_schema(api_url)
            graph = convert_schema_to_rdf(schema)

            # SPARQL query to find all fields for the given entity
            query = prepareQuery(
                """
                SELECT ?field WHERE {
                    ?field rdfs:domain <%(entity_uri)s> .
                }
                """ % {"entity_uri": entity_uri}
            )

            fields = [str(row.field) for row in graph.query(query)]
            return {"entity": entity_uri, "fields": fields}
        except Exception as e:
            return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)