# schema_fetcher.py
from pprint import pprint

import requests
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.requests import RequestsHTTPTransport
from graphql import GraphQLInputObjectType, GraphQLObjectType


def fetch_graphql_schema(api_url):
    transport = AIOHTTPTransport(url=api_url)

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

    client = Client(transport=transport, fetch_schema_from_transport=True)

    response = client.execute(query)
    return client.schema

# schema_parser.py
def parse_schema(schema):
    """
    Parse the schema using gql's client.schema object.
    Extracts queries, entities, fields, and filters.
    """
    queryable_entities = {}

    # Get all query types
    query_type = schema.query_type
    query_fields = query_type.fields if query_type else {}

    # Extract all input and object types
    input_types = {name: type_ for name, type_ in schema.type_map.items() if type_.kind == "INPUT_OBJECT"}
    entity_types = {name: type_ for name, type_ in schema.type_map.items() if type_.kind == "OBJECT"}

    def get_type_name(type_obj):
        """Extracts the base type name from a GraphQL type object."""
        while hasattr(type_obj, "of_type") and type_obj.of_type:
            type_obj = type_obj.of_type
        return type_obj.name

    def expand_input_type(input_type):
        """Recursively expands input object types."""
        if input_type.name not in input_types:
            return input_type.name

        expanded = {}
        for field_name, field in input_type.input_fields.items():
            field_type = get_type_name(field.type)
            if field.type.kind == "INPUT_OBJECT":
                expanded[field_name] = expand_input_type(field.type)
            else:
                expanded[field_name] = field_type

        return expanded

    # Extract queries and their details
    for field_name, field in query_fields.items():
        entity_name = field_name
        entity_type = get_type_name(field.type)
        filters = {}

        # Extract arguments (filters)
        for arg_name, arg in field.args.items():
            arg_type = get_type_name(arg.type)
            if arg.type.kind == "INPUT_OBJECT":
                filters[arg_name] = expand_input_type(arg.type)
            else:
                filters[arg_name] = arg_type

        # Extract entity fields
        entity_fields = {}
        if entity_type in entity_types:
            entity_fields = {
                f_name: get_type_name(f.type)
                for f_name, f in entity_types[entity_type].fields.items()
            }

        queryable_entities[entity_name] = {
            "return_type": entity_type,
            "fields": entity_fields,
            "filters": filters
        }

    return queryable_entities


def extract_fields(graphql_type, visited_types=None):
    """
    Recursively extract fields from GraphQL types while avoiding circular references.
    """
    if visited_types is None:
        visited_types = set()

    # Unwrap lists and non-null types
    while hasattr(graphql_type, 'of_type'):
        graphql_type = graphql_type.of_type

    if not hasattr(graphql_type, 'name'):
        return "UnknownType"

    type_name = graphql_type.name
    if type_name in visited_types:
        return "[Circular Reference]"  # Prevent infinite recursion

    visited_types.add(type_name)
    fields = {}

    if isinstance(graphql_type, GraphQLObjectType) and hasattr(graphql_type, 'fields'):
        for field_name, field in graphql_type.fields.items():
            field_type = field.type
            while hasattr(field_type, 'of_type'):
                field_type = field_type.of_type

            if isinstance(field_type, GraphQLObjectType):  # If it's an object type, recurse
                fields[field_name] = extract_fields(field_type, visited_types.copy())
            else:
                fields[field_name] = field_type.name  # Scalar type

    return fields


def extract_arguments(field):
    """
    Extracts arguments of a GraphQL query or mutation, including nested input objects.
    """
    args = {}
    for arg_name, arg in field.args.items():
        arg_type = arg.type
        while hasattr(arg_type, 'of_type'):
            arg_type = arg_type.of_type  # Unwrap lists and non-null types

        if isinstance(arg_type, GraphQLInputObjectType):  # If argument is an input object
            args[arg_name] = extract_input_object_fields(arg_type)
        else:
            args[arg_name] = arg_type.name  # Scalar or enum type

    return args

def extract_input_object_fields(input_type, visited_types=None):
    """
    Recursively extracts fields from GraphQL input objects.
    """
    if visited_types is None:
        visited_types = set()

    type_name = input_type.name
    if type_name in visited_types:
        return "[Circular Reference]"  # Prevent infinite recursion

    visited_types.add(type_name)
    fields = {}

    if isinstance(input_type, GraphQLInputObjectType):
        for field_name, field in input_type.fields.items():
            field_type = field.type
            while hasattr(field_type, 'of_type'):
                field_type = field_type.of_type

            if isinstance(field_type, GraphQLInputObjectType):
                fields[field_name] = extract_input_object_fields(field_type, visited_types.copy())
            else:
                fields[field_name] = field_type.name  # Scalar or enum type

    return fields


def parse_graphql_schema(schema):
    """
    Parses the GraphQL schema and prints available queries, arguments, and fields.
    """
    query_fields = schema.query_type.fields
    result = {}

    for query_name, query_field in query_fields.items():
        query_info = {
            "arguments": extract_arguments(query_field),  # Extract query arguments
            "fields": extract_fields(query_field.type)  # Extract available fields
        }
        result[query_name] = query_info

    return result



# Assuming `schema` is the result from fetch_graphql_schema(api_url)
schema = fetch_graphql_schema("https://countries.trevorblades.com/")
# schema = fetch_graphql_schema("https://www.universe.com/graphql")
# schema = fetch_graphql_schema("https://beta.pokeapi.co/graphql/v1beta")
parsed_schema = parse_graphql_schema(schema)
# parse_schema2 = parse_schema(schema)

# pprint(schema.type_map["Continent"].fields)
# pprint(schema.query_type.fields)
# pprint(schema.mutation_type)
# pprint(schema.directives)
# pprint(schema.ast_node)
# pprint(schema)
pprint(parsed_schema)
