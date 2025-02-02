def build_fields(fields_list, schema, resource):
    field_strings = []
    for field in fields_list:
        if field in schema[resource]["fields"]:
            field_type = schema[resource]["fields"][field]
            if isinstance(field_type, dict):  # Nested object
                nested_fields = [k for k, v in field_type.items() if v != "[Circular Reference]"]
                nested_fields_str = " ".join(nested_fields)
                field_strings.append(f"{field} {{ {nested_fields_str} }}")
            else:
                field_strings.append(field)
    return " ".join(field_strings)


def build_conditions(conditions):
    condition_parts = []
    for key, value in conditions.items():
        if isinstance(value, dict):
            nested_condition = build_conditions(value)
            condition_parts.append(f"{key}: {{ {nested_condition} }}")
        else:
            condition_parts.append(f'{key}: "{value}"')
    return ", ".join(condition_parts)


def generate_graphql_query(intent, resource, fields, condition_value_dict, schema):
    if not resource or resource not in schema:
        raise ValueError("Invalid resource specified.")

    # Determine the argument key for filtering (e.g., "filter", "where")
    condition_keys = schema[resource].get("arguments", {}).keys()
    condition_arg = next((key for key in condition_keys if isinstance(schema[resource]["arguments"][key], dict)), None)

    condition_str = ""
    if condition_value_dict:
        if condition_arg and condition_arg in condition_value_dict:
            nested_condition_str = build_conditions(condition_value_dict[condition_arg])
            condition_str = f'({condition_arg}: {{ {nested_condition_str} }})'
        else:
            condition_str = f'({build_conditions(condition_value_dict)})'

    fields_str = build_fields(fields, schema, resource)

    query = f"""
    {{
        {resource}{condition_str} {{
            {fields_str}
        }}
    }}
    """

    return query.strip()
