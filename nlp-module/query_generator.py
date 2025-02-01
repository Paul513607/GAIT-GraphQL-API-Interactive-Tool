def generate_graphql_query(intent, resource, fields, conditions, schema):
    """
    Generate a GraphQL query based on the extracted intent, resource, fields, and conditions.
    """
    if not resource or resource not in schema:
        raise ValueError("Invalid resource specified.")

    # Handle object fields correctly
    def format_field(field_name):
        """If a field is an object, return 'field { name }' instead of just 'field'."""
        if field_name in schema[resource]["fields"] and schema[resource]["fields"][field_name] == "OBJECT":
            return f"{field_name} {{ name }}"  # Fetch the name of the object
        return field_name

    formatted_fields = [format_field(field) for field in fields] if fields else ["name"]
    fields_str = "\n".join(formatted_fields)

    # Determine filter structure
    filter_conditions = []
    for condition in conditions:
        field_name = condition["field"]
        value = condition["value"]

        if field_name in schema[resource]["filters"]:
            filter_type = schema[resource]["filters"][field_name]

            if "Filter" in filter_type:  # Means we need nested filters
                filter_conditions.append(f'{field_name}: {{ eq: "{value}" }}')
            else:  # Direct property assignment
                filter_conditions.append(f'{field_name}: "{value}"')

    filter_str = f'filter: {{ {", ".join(filter_conditions)} }}' if filter_conditions else ""

    # Construct the final GraphQL query
    query = f"""
    {{
        {resource}({filter_str}) {{
            {fields_str}
        }}
    }}
    """

    return query.strip()