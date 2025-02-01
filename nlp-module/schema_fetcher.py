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

# Assuming `schema` is the result from fetch_graphql_schema(api_url)
schema = fetch_graphql_schema("https://countries.trevorblades.com/")
parsed_schema = parse_graphql_schema(schema)

pprint(parsed_schema)
