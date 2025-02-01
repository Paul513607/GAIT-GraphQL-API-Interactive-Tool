def map_to_schema(resource, fields, resource_conditions, field_conditions, schema):
    """
    Map extracted entities to the GraphQL schema.
    Handles two types of conditions:
    1. Resource-based conditions (e.g., "continent" in countries(filter: { continent: { eq: "US" } }))
    2. Field-based conditions (e.g., "code" in country(code: "US"))
    """
    # Validate resource
    if resource not in schema:
        raise ValueError(f"Resource '{resource}' not found in schema.")

    # Validate and map fields
    mapped_fields = []
    field_map = schema[resource]["fields"]
    reverse_field_map = {v: k for k, v in field_map.items()}
    for field in fields:
        if field in reverse_field_map:
            mapped_fields.append(field)
        else:
            raise ValueError(f"Field '{field}' not found in resource '{resource}'.")

    # Validate and map resource-based conditions
    mapped_resource_conditions = []
    for condition in resource_conditions:
        field_name = condition["field"]
        value = condition["value"]
        if field_name in schema[resource].get("filters", {}):
            mapped_resource_conditions.append({"field": field_name, "value": value})
        else:
            raise ValueError(f"Condition field '{field_name}' is not valid for resource '{resource}'.")

    # Validate and map field-based conditions
    mapped_field_conditions = []
    for condition in field_conditions:
        field_name = condition["field"]
        value = condition["value"]
        if field_name in schema[resource].get("filters", {}):
            mapped_field_conditions.append({"field": field_name, "value": value})
        else:
            raise ValueError(f"Condition field '{field_name}' is not valid for resource '{resource}'.")

    return resource, mapped_fields, mapped_resource_conditions, mapped_field_conditions