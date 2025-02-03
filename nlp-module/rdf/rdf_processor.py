from rdflib import Graph, Namespace, RDF, RDFS, URIRef, Literal


def convert_schema_to_rdf(schema):
    graph = Graph()
    GRAPHQL = Namespace("http://example.org/graphql#")

    graph.bind("graphql", GRAPHQL)

    for gql_type in schema["types"]:
        type_name = gql_type["name"]
        kind = gql_type["kind"]

        type_uri = URIRef(f"http://example.org/graphql#{type_name}")
        graph.add((type_uri, RDF.type, RDFS.Class))
        graph.add((type_uri, RDFS.label, Literal(type_name)))

        if kind == "OBJECT" and "fields" in gql_type:
            for field in gql_type["fields"]:
                field_name = field["name"]
                field_type = field["type"]["name"]

                field_uri = URIRef(f"http://example.org/graphql#{field_name}")
                graph.add((field_uri, RDF.type, RDF.Property))
                graph.add((field_uri, RDFS.label, Literal(field_name)))

                if field_type:
                    field_type_uri = URIRef(f"http://example.org/graphql#{field_type}")
                    graph.add((field_uri, RDFS.range, field_type_uri))
                    graph.add((type_uri, RDFS.subClassOf, field_type_uri))

    return graph    