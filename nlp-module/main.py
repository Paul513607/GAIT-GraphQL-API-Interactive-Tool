import os

from flask import Flask, request, jsonify

from openai_model import openai_model
from nlp_custom_model import nlp_main

app = Flask(__name__)

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


if __name__ == "__main__":
    app.run(debug=True)
