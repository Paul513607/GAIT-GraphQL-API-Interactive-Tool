from collections.abc import Mapping

import spacy
from nltk.corpus import wordnet
import nltk

nlp = spacy.load("en_core_web_md")
nltk.download('wordnet')
nltk.download('omw-1.4')

def merge_dicts(dict1, dict2):
    """ Recursively merge two dictionaries. """
    for key, value in dict2.items():
        if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, Mapping):
            merge_dicts(dict1[key], value)
        else:
            dict1[key] = value
    return dict1

def get_synonyms(word):
    """Get synonyms for a word using WordNet."""
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().replace("_", " "))
    return list(synonyms)

def advanced_intent_detection(doc_main):
    """Detect user intent with expanded vocabulary."""
    intent_synonyms = {
        "fetch": get_synonyms("get") + get_synonyms("fetch") + get_synonyms("find") + get_synonyms("list"),
        "filter": get_synonyms("filter") + get_synonyms("search") + get_synonyms("where") + ["show me", "display"],
    }

    for token in doc_main:
        for intent_type, synonyms in intent_synonyms.items():
            if token.text in synonyms:
                return intent_type
    return "fetch"  # Default intent

def split_request_and_condition(query):
    """
    Split a user query into the request part and the condition part.
    """
    # Process the query with spaCy
    doc = nlp(query.lower())

    # Prepositions that typically introduce conditions
    condition_prepositions = {"with", "by", "where"}

    # Find the first preposition that introduces the condition
    split_index = None
    for token in doc:
        if token.text in condition_prepositions:
            split_index = token.i
            break

    # Split the query into request and condition
    if split_index is not None:
        request = doc[:split_index].text
        condition = doc[split_index + 1:].text
    else:
        request = query
        condition = ""

    return request, condition

def extract_resource_and_fields(doc_main, schema):
    """Identify resources and fields in user query."""
    resource = None
    mentioned_fields = {}

    for token in doc_main:
        # Check if token matches any resource in the schema
        if token.text in schema:
            resource = token.text
            break

    if resource:
        # Collect fields mentioned in the query
        all_fields = list(schema[resource]["fields"].keys())
        doc_main_str = doc_main.text.lower()

        for field in all_fields:
            if field.lower() in doc_main_str:
                if isinstance(schema[resource]["fields"][field], dict):
                    # remove the keys that have [Circular Reference] as value
                    filtered_fields = {k: v for k, v in schema[resource]["fields"][field].items() if v != "[Circular Reference]"}
                    mentioned_fields[field] = list(filtered_fields.keys())
                else:
                    mentioned_fields[field] = None

        if not mentioned_fields:
            for field in all_fields:
                if isinstance(schema[resource]["fields"][field], dict):
                    # remove the keys that have [Circular Reference] as value
                    filtered_fields = {k: v for k, v in schema[resource]["fields"][field].items() if
                                       v != "[Circular Reference]"}
                    mentioned_fields[field] = list(filtered_fields.keys())
                else:
                    mentioned_fields[field] = None

    return resource, mentioned_fields


def find_key_path(dictionary, target_key, path=None):
    if path is None:
        path = []

    if isinstance(dictionary, dict):
        if target_key in dictionary:
            return path + [target_key]

        for key, value in dictionary.items():
            new_path = find_key_path(value, target_key, path + [key])
            if new_path is not None:
                return new_path
    return None

def build_nested_dict(keys, value):
    """
    Build a nested dictionary from a list of keys and a value.
    Example:
        keys = ["filter", "code", "eq"]
        value = "US"
        Output: {"filter": {"code": {"eq": "US"}}}
    """
    nested_dict = {}
    current_level = nested_dict

    # Iterate through the keys and build the nested structure
    for key in keys[:-1]:  # All keys except the last one
        current_level[key] = {}
        current_level = current_level[key]

    # Add the final key-value pair
    current_level[keys[-1]] = value

    return nested_dict


def extract_conditions(doc_main, schema, resource):
    """
    Extracts conditions from a user query based on the schema.
    Supports multiple key paths for each field mentioned in the subquery.
    """
    tokens = [token.text for token in doc_main]
    condition_value_dict = {}

    # Collect all key paths
    key_paths = []
    for token in doc_main:
        if token.text in schema[resource]["fields"]:
            key_path = find_key_path(schema[resource]["arguments"], token.text)
            if key_path:
                key_paths.append(key_path)  # Store multiple paths

    if resource and resource in schema:
        filter_mapping = schema[resource].get("arguments", {})

        for key_path in key_paths:
            temp_filter_mapping = filter_mapping  # Reset filter mapping for each key_path

            # Navigate through key_path
            for key in key_path[:-1]:
                if key in temp_filter_mapping:
                    temp_filter_mapping = temp_filter_mapping[key]

            last_key = key_path[-1]

            for token in doc_main:
                normalized_token = token.lemma_.lower()

                matched_filter = None
                for filter_key in temp_filter_mapping:
                    if normalized_token == filter_key or normalized_token in get_synonyms(filter_key):
                        matched_filter = filter_key
                        break

                if matched_filter:
                    condition_value = None
                    operator = None

                    if isinstance(temp_filter_mapping[matched_filter], dict):
                        operator = list(temp_filter_mapping[matched_filter].keys())[0]

                    # Append operator if available
                    full_key_path = key_path + [operator] if operator else key_path

                    # Extract condition value
                    for child in token.children:
                        if child.dep_ in {"attr", "prep", "dobj", "pobj"} or child.pos_ in {"NUM", "NOUN", "PROPN"}:
                            condition_value = child.text
                            break

                    # Check named entities (like country codes)
                    if not condition_value:
                        for ent in doc_main.ents:
                            if ent.start == token.i + 1:
                                condition_value = ent.text
                                break

                    # Append only if we got a value
                    if condition_value:
                        temp_dict = build_nested_dict(full_key_path, condition_value)
                        condition_value_dict = merge_dicts(condition_value_dict, temp_dict)

    return condition_value_dict

def extract_resource_fields_and_conditions(doc_main, schema):
    """Extract resources, fields, and conditions from user query."""
    request, condition = split_request_and_condition(doc_main.text)
    doc_request = nlp(request)
    doc_condition = nlp(condition)
    resource, fields = extract_resource_and_fields(doc_request, schema)
    condition_value_dict = extract_conditions(doc_condition, schema, resource)
    return resource, fields, condition_value_dict