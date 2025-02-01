# main.py
from nlp_processor import normalize_schema, extract_intent_and_entities
from query_generator import generate_graphql_query
from schema_fetcher import fetch_graphql_schema, parse_schema


def main():
    # Step 1: Fetch and parse schema
    api_url = "https://www.universe.com/graphql"
    # api_url = "https://countries.trevorblades.com/"
    schema = fetch_graphql_schema(api_url)
    parsed_schema = parse_schema(schema)
    normalized_schema = normalize_schema(parsed_schema)

    while True:
        try:
            # Step 2: Get user input
            user_query = input("\nEnter your query (or 'quit' to exit): ")
            if user_query.lower() == 'quit':
                break

            # Step 3: Process the query
            intent, resource, fields, resource_conditions, field_conditions = extract_intent_and_entities(
                user_query, parsed_schema, normalized_schema
            )

            # Step 4: Generate the query
            query = generate_graphql_query(
                intent, resource, fields, resource_conditions, field_conditions, parsed_schema
            )

            print("\nGenerated GraphQL Query:")
            print(query)

            # Step 5: Execute the query (optional)
            # response = requests.post(api_url, json={'query': query})
            # print("\nResponse:")
            # print(json.dumps(response.json(), indent=2))

        except ValueError as e:
            print(f"\nError: {e}")
        except Exception as e:
            print(f"\nUnexpected error: {e}")

if __name__ == "__main__":
    main()
