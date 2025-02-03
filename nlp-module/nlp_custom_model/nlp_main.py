from nlp_custom_model.nlp_processor import nlp, advanced_intent_detection, \
    extract_resource_fields_and_conditions
from nlp_custom_model.query_generator import generate_graphql_query
from common.schema_fetcher import fetch_graphql_schema, parse_graphql_schema


def get_graphql_query(api_url, user_query):
    schema, _ = fetch_graphql_schema(api_url)
    parsed_schema = parse_graphql_schema(schema)

    doc_main = nlp(user_query)
    intent = advanced_intent_detection(doc_main)
    resource, fields, condition_value_dict = extract_resource_fields_and_conditions(doc_main, parsed_schema)

    if resource:
        query = generate_graphql_query(intent, resource, fields, condition_value_dict, parsed_schema)
        print("\nGenerated GraphQL Query:", query)
        return query
    else:
        print("Resource not recognized. Please try again.")
        return None


if __name__ == "__main__":
    api_url = "https://countries.trevorblades.com/"
    user_query = "get country with code AF"
    get_graphql_query(api_url, user_query)
