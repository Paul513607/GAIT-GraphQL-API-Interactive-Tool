def map_to_schema(resource, fields, conditions, schema):
    """
    Map extracted entities to the GraphQL schema.
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

    # Validate and map conditions
    mapped_conditions = []
    filter_list = schema[resource].get("filters", {})

    for condition in conditions:
        if condition["field"] in filter_list:
            mapped_conditions.append({"field": condition["field"], "value": condition["value"]})
        else:
            raise ValueError(f"Condition field '{condition['field']}' is not valid for resource '{resource}'.")

    return resource, mapped_fields, mapped_conditions
