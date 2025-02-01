from schema_fetcher import fetch_graphql_schema
from schema_parser import parse_schema
from nlp_processor import (
    normalize_schema,
    extract_intent_and_entities,
    detect_intent,
    extract_resource,
    extract_fields,
    extract_conditions,
)
from query_generator import generate_graphql_query
from util import map_to_schema

def main():
    # Step 1: Fetch and parse the GraphQL schema
    api_url = "https://countries.trevorblades.com/"  # Example public GraphQL API
    schema = fetch_graphql_schema(api_url)
    parsed_schema = parse_schema(schema)
    normalized_schema = normalize_schema(parsed_schema)

    # Step 2: Accept user input
    user_query = 'Find countries with code US'

    # Step 3: Extract intent and entities
    intent, resource, fields, conditions = extract_intent_and_entities(user_query, normalized_schema)

    # Step 4: Map extracted entities to the schema
    try:
        resource, mapped_fields, mapped_conditions = map_to_schema(resource, fields, conditions, parsed_schema)
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Step 5: Generate the GraphQL query
    try:
        graphql_query = generate_graphql_query(intent, resource, mapped_fields, mapped_conditions, parsed_schema)
        print("\nGenerated GraphQL Query:")
        print(graphql_query)
    except ValueError as e:
        print(f"Error generating query: {e}")

if __name__ == "__main__":
    main()