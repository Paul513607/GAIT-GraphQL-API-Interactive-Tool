from flask import Flask, Response, request, jsonify

from common.schema_fetcher import fetch_graphql_schema
from openai_model import openai_model
from nlp_custom_model import nlp_main
from rdf.rdf_processor import convert_schema_to_rdf
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/generate_query', methods=['GET'])
def generate_query():
    api_url = request.args.get('api_url')
    user_input = request.args.get('user_input')
    model = request.args.get('model')

    if not api_url or not user_input or not model:
        return jsonify({"error": "Missing required parameters"}), 400
    if model == "openai":
        try:
            query = openai_model.generate_graphql_query(api_url, user_input)
            return jsonify({"query": query})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    elif model == "custom":
        try:
            query = nlp_main.get_graphql_query(api_url, user_input)
            if not query:
                return jsonify({"error": "Resource not recognized. Please try again."}), 400
            return jsonify({"query": query})
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route('/generate_rdf', methods=['GET'])
def generate_rdf():
    api_url = request.args.get('api_url')

    if not api_url:
        return jsonify({"error": "Missing required parameter: api_url"}), 400

    try:
        _, schema = fetch_graphql_schema(api_url)
        rdf_data = convert_schema_to_rdf(schema)
        return Response(rdf_data, mimetype="text/turtle")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
