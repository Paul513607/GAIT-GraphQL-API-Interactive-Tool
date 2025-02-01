import spacy
import nltk
from nltk.corpus import wordnet
from pprint import pprint

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Ensure NLTK WordNet is downloaded
nltk.download('wordnet')
# schema_fetcher.py
from pprint import pprint

import requests
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.requests import RequestsHTTPTransport

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
    pprint(response['__schema'])
    return response['__schema']

# schema_parser.py
def parse_schema(schema):
    """
    Parse the schema to extract entities, fields, and filters.
    """
    query_type_name = schema['queryType']['name']
    query_types = {t['name']: t for t in schema['types'] if t['name'] == query_type_name}
    input_types = {t['name']: t for t in schema['types'] if t['kind'] == "INPUT_OBJECT"}
    entity_types = {t['name']: t for t in schema['types'] if t['kind'] == "OBJECT"}

    queryable_entities = {}

    def get_type_name(type_obj):
        while type_obj and 'ofType' in type_obj and type_obj['ofType']:
            type_obj = type_obj['ofType']
        return type_obj.get('name', type_obj.get('kind', 'UNKNOWN'))

    def expand_input_type(input_type_name):
        if input_type_name not in input_types:
            return input_type_name

        expanded = {}
        for field in input_types[input_type_name]['inputFields']:
            field_name = field['name']
            field_type = get_type_name(field['type'])

            if field['type']['kind'] == "INPUT_OBJECT":
                expanded[field_name] = expand_input_type(field_type)
            else:
                expanded[field_name] = field_type

        return expanded

    if query_type_name in query_types:
        query_fields = query_types[query_type_name]['fields']
        for field in query_fields:
            entity_name = field['name']
            entity_type = get_type_name(field['type'])
            args = field.get('args', [])
            filters = {}

            if args:
                for arg in args:
                    arg_name = arg['name']
                    arg_type = get_type_name(arg['type'])

                    if arg['type']['kind'] == "INPUT_OBJECT" and arg_type in input_types:
                        filters[arg_name] = expand_input_type(arg_type)
                    else:
                        filters[arg_name] = arg_type

            entity_fields = {}
            if entity_type in entity_types:
                entity_fields = {
                    f['name']: get_type_name(f['type'])
                    for f in entity_types[entity_type]['fields']
                }

            queryable_entities[entity_name] = {
                "return_type": entity_type,
                "fields": entity_fields,
                "filters": filters
            }

    return queryable_entities

def parse_graphql_schema(schema):
    queryable_entities = {}

    # Extract query types
    query_type = schema.get('queryType', {}).get('name')
    queryable_entities['queries'] = {}

    if query_type:
        query_fields = [t for t in schema['types'] if t['name'] == query_type][0]['fields']
        for field in query_fields:
            queryable_entities['queries'][field['name']] = {
                'args': {arg['name']: arg['type'] for arg in field.get('args', [])},
                'return_type': field['type']
            }

    # Extract mutations if available
    mutation_type = schema.get('mutationType', {}).get('name')
    if mutation_type:
        mutation_fields = [t for t in schema['types'] if t['name'] == mutation_type][0]['fields']
        queryable_entities['mutations'] = {}
        for field in mutation_fields:
            queryable_entities['mutations'][field['name']] = {
                'args': {arg['name']: arg['type'] for arg in field.get('args', [])},
                'return_type': field['type']
            }

    # Extract object types
    object_types = {t['name']: t for t in schema['types'] if t['kind'] == 'OBJECT'}
    queryable_entities['object_types'] = object_types

    return queryable_entities

def get_synonyms(word):
    """Returns synonyms for a given word using NLTK's WordNet"""
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().lower())
    return synonyms


def match_query(user_input, parsed_schema):
    """Matches user input with GraphQL queries using spaCy & NLTK synonyms"""
    doc = nlp(user_input)

    # Extract nouns & proper nouns (likely entities)
    keywords = {token.text.lower() for token in doc if token.pos_ in ['NOUN', 'PROPN']}

    # Expand keywords with synonyms
    expanded_keywords = set()
    for word in keywords:
        expanded_keywords.add(word)
        expanded_keywords.update(get_synonyms(word))

    # Match against GraphQL queries
    best_match = None
    best_score = 0

    for query_name, query_details in parsed_schema['queries'].items():
        query_keywords = {query_name.lower()}
        query_keywords.update(get_synonyms(query_name.lower()))

        # Calculate match score
        score = len(expanded_keywords & query_keywords)
        if score > best_score:
            best_match = query_name
            best_score = score

    return best_match


def generate_graphql_query(user_input, parsed_schema):
    """Generates a GraphQL query based on user input"""
    matched_query = match_query(user_input, parsed_schema)

    if not matched_query:
        return "No matching query found."

    query_details = parsed_schema['queries'][matched_query]

    # Create a sample query
    args = query_details['args']
    query_args = ", ".join(f"{arg}: \"example_value\"" for arg in args)

    graphql_query = f"""
    query {{
        {matched_query}({query_args}) {{
            {", ".join(args.keys())}  # Selecting all available fields
        }}
    }}
    """

    return graphql_query


# Example Usage
user_input = "Get country with code US"
parsed_schema = parse_graphql_schema(fetch_graphql_schema("https://countries.trevorblades.com/"))
graphql_query = generate_graphql_query(user_input, parsed_schema)

print(graphql_query)
