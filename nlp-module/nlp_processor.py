import spacy
from nltk.corpus import wordnet
import nltk

nlp = spacy.load("en_core_web_md")
nltk.download('wordnet')
nltk.download('omw-1.4')


def get_synonyms(word):
    """Get synonyms for a word using WordNet."""
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())
    return list(synonyms)


def normalize_term(term):
    """Normalize a term using spaCy's lemmatization."""
    return nlp(term)[0].lemma_


def normalize_schema(schema):
    """
    Normalize only the entity names in the schema, keeping original field names.
    """
    normalized_schema = {}

    for entity, details in schema.items():
        normalized_entity = normalize_term(entity)

        normalized_schema[normalized_entity] = {
            "original": entity,
            "fields": details["fields"],  # Keep original field names
            "filters": details.get("filters", {}),  # Keep original filter names
            "return_type": details["return_type"]
        }

    return normalized_schema


def extract_intent_and_entities(query, schema, normalized_schema):
    """
    Extract intent and entities from the query.
    Now handles conditional splitting and better field extraction.
    """
    # Define conditional prepositions
    condition_prepositions = ["in", "with", "by", "for"]

    # Split query into main part and condition part
    main_query = query
    condition_query = ""

    # Find the first condition preposition and split
    tokens = query.split()
    for i, token in enumerate(tokens):
        if token.lower() in condition_prepositions:
            main_query = " ".join(tokens[:i])
            condition_query = " ".join(tokens[i + 1:])  # Skip the preposition
            break

    # Process main query with spaCy
    doc_main = nlp(main_query.lower())

    # Detect intent
    intent_synonyms = {
        "fetch": get_synonyms("get") + get_synonyms("fetch") + get_synonyms("find") + get_synonyms("list"),
        "filter": get_synonyms("filter") + get_synonyms("search") + get_synonyms("where"),
    }

    intent = None
    for token in doc_main:
        for intent_type, synonyms in intent_synonyms.items():
            if token.text in synonyms:
                intent = intent_type
                break
        if intent:
            break

    if not intent:
        intent = "fetch"  # Default intent

    # Extract resource
    resource = None
    for token in doc_main:
        if token.text in schema:
            resource = token.text
            break

    if not resource:
        raise ValueError("Could not identify a valid resource in the query")

    # Get all available fields for the resource
    normalized_resource = normalize_term(resource)
    all_fields = list(schema[resource]["fields"].keys())  # Use original schema instead of normalized

    # Extract specifically mentioned fields from main query
    mentioned_fields = []
    doc_main_str = doc_main.text.lower()

    for field in all_fields:
        if field.lower() in doc_main_str:
            mentioned_fields.append(field)

    # Use mentioned fields if any were found, otherwise use all fields
    fields = mentioned_fields if mentioned_fields else all_fields

    # Process conditions if they exist
    resource_conditions = []
    field_conditions = []

    if condition_query:
        doc_condition = nlp(condition_query.lower())
        tokens = [token for token in doc_condition]

        for i, token in enumerate(tokens):
            # Check if current token is a filter field
            normalized_token = normalize_term(token.text)

            # Try to get the next token as the value
            next_value = None
            if i + 1 < len(tokens):
                next_value = tokens[i + 1].text.upper()  # Keep the value in its original form

            if next_value:
                # Check for resource-based conditions
                if resource in schema and token.text in schema[resource]["fields"]:
                    resource_conditions.append({
                        "field": token.text,
                        "value": next_value
                    })
                # Check for field-based conditions
                elif resource:
                    if "filter" in schema[resource]["filters"]:
                        filter_fields = schema[resource]["filters"]["filter"]
                        # Check if the normalized token matches any filter field
                        if normalized_token in [normalize_term(f) for f in filter_fields]:
                            field_conditions.append({
                                "field": token.text,
                                "value": next_value
                            })

    # if condition_query:
    #     doc_condition = nlp(condition_query.lower())
    #
    #     # Extract values after prepositions
    #     for token in doc_condition:
    #         if token.text in condition_prepositions:
    #             # Look at the next tokens for values
    #             next_token = token.nbor(1) if token.i + 1 < len(doc_condition) else None
    #             if next_token:
    #                 # Check if it matches any filter fields
    #                 normalized_token = normalize_term(next_token.text)
    #
    #                 # Check for resource-based conditions
    #                 if normalized_token in schema:
    #                     resource_conditions.append({
    #                         "field": normalized_schema[normalized_token]["original"],
    #                         "value": next_token.text
    #                     })
    #                 # Check for field-based conditions
    #                 elif resource:
    #                     field_filters = normalized_schema[normalized_resource]["filters"]
    #                     for filter_field in field_filters:
    #                         if normalize_term(filter_field) == normalized_token:
    #                             field_conditions.append({
    #                                 "field": filter_field,
    #                                 "value": next_token.text
    #                             })
    return intent, resource, fields, resource_conditions, field_conditions