import spacy
from nltk.corpus import wordnet
import nltk

# Load spaCy's English model with word vectors
nlp = spacy.load("en_core_web_md")  # Medium model with word vectors

# Download WordNet data (if not already downloaded)
nltk.download('wordnet')
nltk.download('omw-1.4')


def get_synonyms(word):
    """
    Get synonyms for a word using WordNet.
    """
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())
    return list(synonyms)


def normalize_term(term):
    """
    Normalize a term using spaCy's lemmatization.
    """
    return nlp(term)[0].lemma_


def normalize_schema(schema):
    """
    Normalize the schema terms (entities and fields) for consistent matching.
    """
    normalized_schema = {}

    for entity, details in schema.items():
        normalized_entity = normalize_term(entity)

        # Create a mapping {normalized_field: original_field}
        field_mapping = {normalize_term(field): field for field in details["fields"]}

        # Create a mapping {normalized_filter: original_filter}
        filter_mapping = {normalize_term(field): field for field in details.get("filters", {})}

        normalized_schema[normalized_entity] = {
            "fields": field_mapping,
            "filters": filter_mapping
        }

    return normalized_schema


def detect_intent(query):
    """
    Detect the intent of the query using WordNet synonyms.
    """
    doc = nlp(query.lower())
    intent_synonyms = {
        "fetch": get_synonyms("get") + get_synonyms("fetch") + get_synonyms("find") + get_synonyms("list"),
        "filter": get_synonyms("filter") + get_synonyms("search") + get_synonyms("where"),
    }
    for token in doc:
        for intent, synonyms in intent_synonyms.items():
            if token.text in synonyms:
                return intent
    return None


def extract_resource(query, schema):
    """
    Extract the resource (entity) from the query.
    """
    doc = nlp(query.lower())

    for token in doc:
        normalized_token = normalize_term(token.text)
        if normalized_token in schema:
            return normalized_token

    return None

def extract_fields(query, resource, schema):
    """
    Extract the fields from the query.
    """
    doc = nlp(query.lower())
    fields = []

    if resource and resource in schema:
        field_mapping = schema[resource]["fields"]  # {normalized_field: original_field}

        for chunk in doc.noun_chunks:  # Using noun chunks to identify field names
            normalized_chunk = normalize_term(chunk.text)
            if normalized_chunk in field_mapping:
                fields.append(field_mapping[normalized_chunk])  # Store original field name

        # Also check individual tokens
        for token in doc:
            normalized_token = normalize_term(token.text)
            if normalized_token in field_mapping and field_mapping[normalized_token] not in fields:
                fields.append(field_mapping[normalized_token])  # Store original field name

    return fields if fields else list(schema[resource]["fields"].values())  # Default to all fields if none specified


def extract_conditions(query, resource, schema):
    """
    Extract the conditions from the query.
    """
    doc = nlp(query.lower())
    conditions = []

    if resource and resource in schema:
        filter_mapping = schema[resource]["filters"]  # {normalized_filter: original_filter}

        for token in doc:
            normalized_token = normalize_term(token.text)

            if normalized_token in filter_mapping:
                original_filter = filter_mapping[normalized_token]

                # Try to extract the correct value for the condition
                condition_value = None

                # Look at the next token for a potential value
                next_token = token.nbor(1) if token.i + 1 < len(doc) else None
                if next_token and next_token.pos_ in {"NUM", "NOUN", "PROPN", "ADJ"}:
                    condition_value = next_token.text

                # If no valid next token, check the dependency tree
                if not condition_value:
                    for child in token.children:
                        if child.pos_ in {"NUM", "NOUN", "PROPN", "ADJ"}:
                            condition_value = child.text
                            break

                # Ensure we actually got a value before appending
                if condition_value:
                    conditions.append({"field": original_filter, "value": condition_value})

    return conditions


def extract_intent_and_entities(query, schema):
    """
    Extract intent and entities from the query.
    """
    condition_prepositions = ["in", "with", "by"]

    tokens = query.split()

    resource_subquery = query
    condition_subquery = query

    # Split the query into resource_subquery and condition_subquery
    for prep in condition_prepositions:
        if prep in tokens:
            resource_subquery = query.split(prep)[0]
            condition_subquery = query.split(prep)[1]
            break

    # Detect intent
    intent = detect_intent(resource_subquery)

    # Extract resource
    resource = extract_resource(resource_subquery, schema)

    # Extract fields
    fields = extract_fields(resource_subquery, resource, schema)

    # Extract conditions
    conditions = extract_conditions(condition_subquery, resource, schema)

    return intent, resource, fields, conditions