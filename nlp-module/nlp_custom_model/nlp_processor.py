from collections.abc import Mapping

import spacy
from nltk.corpus import wordnet
import nltk

nlp = spacy.load("en_core_web_md")
nltk.download('wordnet')
nltk.download('omw-1.4')


def merge_dicts(dict1, dict2):
    for key, value in dict2.items():
        if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, Mapping):
            merge_dicts(dict1[key], value)
        else:
            dict1[key] = value
    return dict1


def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().replace("_", " "))
    return list(synonyms)


def advanced_intent_detection(doc_main):
    intent_synonyms = {
        "fetch": get_synonyms("get") + get_synonyms("fetch") + get_synonyms("find") + get_synonyms("list"),
        "filter": get_synonyms("filter") + get_synonyms("search") + get_synonyms("where") + ["show me", "display"],
    }

    for token in doc_main:
        for intent_type, synonyms in intent_synonyms.items():
            if token.text in synonyms:
                return intent_type
    return "fetch"  # Default


def split_request_and_condition(query):
    doc = nlp(query)

    condition_prepositions = {"with", "by", "where"}

    split_index = None
    for token in doc:
        if token.text in condition_prepositions:
            split_index = token.i
            break

    if split_index is not None:
        request = doc[:split_index].text
        condition = doc[split_index + 1:].text
    else:
        request = query
        condition = ""

    return request, condition


def extract_resource_and_fields(doc_main, schema):
    resource = None
    mentioned_fields = {}

    for token in doc_main:
        if token.text in schema:
            resource = token.text
            break

    if resource:
        all_fields = list(schema[resource]["fields"].keys())
        doc_main_str = doc_main.text

        for field in all_fields:
            if field.lower() in doc_main_str:
                if isinstance(schema[resource]["fields"][field], dict):
                    # remove the keys that have [Circular Reference] as value
                    filtered_fields = {k: v for k, v in schema[resource]["fields"][field].items() if
                                       v != "[Circular Reference]"}
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
    nested_dict = {}
    current_level = nested_dict

    for key in keys[:-1]:
        current_level[key] = {}
        current_level = current_level[key]

    current_level[keys[-1]] = value

    return nested_dict


def extract_conditions(doc_main, schema, resource):
    tokens = [token.text for token in doc_main]
    condition_value_dict = {}

    key_paths = []
    for token in doc_main:
        if token.text in schema[resource]["fields"]:
            key_path = find_key_path(schema[resource]["arguments"], token.text)
            if key_path:
                key_paths.append(key_path)

    if resource and resource in schema:
        filter_mapping = schema[resource].get("arguments", {})

        for key_path in key_paths:
            temp_filter_mapping = filter_mapping

            # Navigate through key_path
            for key in key_path[:-1]:
                if key in temp_filter_mapping:
                    temp_filter_mapping = temp_filter_mapping[key]

            for token in doc_main:
                if token.text != key_path[-1]:
                    continue
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

                    full_key_path = key_path + [operator] if operator else key_path

                    for child in token.children:
                        if child.dep_ in {"attr", "prep", "dobj", "pobj"} or child.pos_ in {"NUM", "NOUN", "PROPN"}:
                            condition_value = child.text
                            break

                    if not condition_value:
                        condition_value = doc_main[token.i + 1].text

                    if condition_value:
                        temp_dict = build_nested_dict(full_key_path, condition_value)
                        condition_value_dict = merge_dicts(condition_value_dict, temp_dict)
                        break

    return condition_value_dict


def extract_resource_fields_and_conditions(doc_main, schema):
    request, condition = split_request_and_condition(doc_main.text)
    doc_request = nlp(request)
    doc_condition = nlp(condition)
    resource, fields = extract_resource_and_fields(doc_request, schema)
    condition_value_dict = extract_conditions(doc_condition, schema, resource)
    return resource, fields, condition_value_dict
