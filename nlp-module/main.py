# main.py
from nlp_processor import nlp, advanced_intent_detection, \
    extract_resource_and_fields, extract_resource_fields_and_conditions
from query_generator import generate_graphql_query
from schema_fetcher import fetch_graphql_schema, parse_schema, parse_graphql_schema


def main():
    api_url = "https://countries.trevorblades.com/"
    schema = fetch_graphql_schema(api_url)
    parsed_schema = parse_graphql_schema(schema)

    i = 1
    while i == 1:
        i += 1
        user_query = "get country name with code ro"
        if user_query.lower() == 'quit':
            break

        doc_main = nlp(user_query.lower())
        intent = advanced_intent_detection(doc_main)
        resource, fields, condition_value_dict = extract_resource_fields_and_conditions(doc_main, parsed_schema)

        if resource:
            query = generate_graphql_query(intent, resource, fields, condition_value_dict, parsed_schema)
            print("\nGenerated GraphQL Query:")
            print(query)
        else:
            print("Resource not recognized. Please try again.")


if __name__ == "__main__":
    main()
