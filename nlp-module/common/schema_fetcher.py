from pprint import pprint

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
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

    result = client.execute(query)
    return client.schema, result['__schema']


def extract_fields(graphql_type, visited_types=None):
    if visited_types is None:
        visited_types = set()

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
    args = {}
    for arg_name, arg in field.args.items():
        arg_type = arg.type
        while hasattr(arg_type, 'of_type'):
            arg_type = arg_type.of_type

        if isinstance(arg_type, GraphQLInputObjectType):
            args[arg_name] = extract_input_object_fields(arg_type)
        else:
            args[arg_name] = arg_type.name

    return args


def extract_input_object_fields(input_type, visited_types=None):
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
    query_fields = schema.query_type.fields
    result = {}

    for query_name, query_field in query_fields.items():
        query_info = {
            "arguments": extract_arguments(query_field),  # Extract query arguments
            "fields": extract_fields(query_field.type)  # Extract fields
        }
        result[query_name] = query_info

    return result


if __name__ == "__main__":
    # schema = fetch_graphql_schema("https://countries.trevorblades.com/")
    # schema = fetch_graphql_schema("https://portal.ehri-project.eu/api/graphql")
    schema = fetch_graphql_schema("https://api.tcgdex.net/v2/graphql")
    parsed_schema, _ = parse_graphql_schema(schema)
    pprint(parsed_schema)
