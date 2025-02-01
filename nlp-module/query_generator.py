# query_generator.py
def generate_graphql_query(intent, resource, fields, resource_conditions, field_conditions, schema):
    if not resource or resource not in schema:
        raise ValueError(f"Invalid resource: {resource}")

    def build_fields(fields_list, current_resource):
        field_strings = []
        resource_info = schema[current_resource]

        for field in fields_list:
            field_type = resource_info["fields"].get(field)
            if not field_type:
                continue

            if field in resource_info["fields"] and field_type in schema:
                nested_fields = get_default_fields(field_type)
                field_strings.append(f"{field} {{ {nested_fields} }}")
            else:
                field_strings.append(field)

        # TODO: FIX THIS
        if len(field_strings) == 0:
            return "name"
        else:
            return " ".join(field_strings)

    def get_default_fields(resource_type):
        if resource_type not in schema:
            return "id name"

        default_fields = []
        for field, field_type in schema[resource_type]["fields"].items():
            if field_type not in schema:
                default_fields.append(field)
                if len(default_fields) >= 3:
                    break
        return " ".join(default_fields)

    # Build filter conditions
    filter_args = []

    if resource_conditions:
        filter_dict = {}
        for condition in resource_conditions:
            field = condition["field"]
            value = condition["value"]

            if "filters" in schema[resource] and "filter" in schema[resource]["filters"]:
                filter_dict[field] = {"eq": value}
            else:
                field_conditions.append(condition)

        if filter_dict:
            filter_str = "filter: {"
            for field, ops in filter_dict.items():
                filter_str += f"{field}: {{"
                for op, val in ops.items():
                    filter_str += f'{op}: "{val}"'
                filter_str += "}"
            filter_str += "}"
            filter_args.append(filter_str)

    if field_conditions:
        for condition in field_conditions:
            field = condition["field"]
            value = condition["value"]
            filter_args.append(f'{field}: "{value}"')

    args_str = f'({", ".join(filter_args)})' if filter_args else ""
    fields_str = build_fields(fields, resource)
    if not fields_str:
        fields_str = get_default_fields(resource)

    query = f"""query {{
              {resource}{args_str} {{
                {fields_str}
                  }}
                }}"""

    return query