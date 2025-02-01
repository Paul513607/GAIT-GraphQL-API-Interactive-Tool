def parse_schema(schema):
    """
    Parse the schema to extract:
    - Entities and their selectable fields
    - Filterable fields and their expected format
    """
    queryable_entities = {}

    # Step 1: Identify input types (used for filtering)
    input_types = {}
    for type_info in schema:
        if type_info.get("inputFields"):
            input_types[type_info["name"]] = {
                field["name"]: determine_field_type(field["type"])
                for field in type_info["inputFields"]
            }

    # Step 2: Identify queryable entities and their fields
    for type_info in schema:
        if type_info.get("fields") and type_info["kind"] == "OBJECT":
            entity_name = type_info["name"].lower()
            fields = {}
            filters = {}

            # Extract selectable fields
            for field in type_info["fields"]:
                field_name = field["name"]
                field_type = determine_field_type(field["type"])
                fields[field_name] = field_type

                # Check if the field supports filtering (by looking at its arguments)
                for arg in field.get("args", []):
                    arg_name = arg["name"]
                    arg_type = determine_field_type(arg["type"])

                    if "filter" in arg_name.lower():  # GraphQL typically uses "filter" in the name
                        if arg_type in input_types:  # If it's a known filter type, expand it
                            filters[arg_name] = input_types[arg_type]
                        else:
                            filters[arg_name] = arg_type  # Otherwise, store as-is

            queryable_entities[entity_name] = {
                "fields": fields,
                "filters": filters
            }

    return queryable_entities


def determine_field_type(type_info):
    """
    Determine the actual type of a field or argument.
    Handles nested GraphQL types (e.g., NON_NULL, LIST, OBJECT).
    """
    if not type_info:
        return None

    kind = type_info.get("kind")
    name = type_info.get("name")
    of_type = type_info