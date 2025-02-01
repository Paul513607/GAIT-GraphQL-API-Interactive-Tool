import spacy
import nltk
from nltk.corpus import wordnet
import requests
import json

nltk.download('wordnet')
nltk.download('omw-1.4')


class GraphQLNLPParser:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.schema = self.fetch_schema()
        self.nlp = spacy.load("en_core_web_md")  # Using medium model for better word vectors

    def fetch_schema(self):
        """
        Fetches the GraphQL schema using introspection.
        """
        query = """
        {
          __schema {
            types {
              name
              fields {
                name
                type {
                  name
                  kind
                }
              }
            }
          }
        }
        """
        response = requests.post(self.endpoint, json={'query': query})
        if response.status_code == 200:
            return response.json()["data"]["__schema"]["types"]
        return None

    def get_synonyms(self, word):
        """
        Retrieves synonyms for a given word using WordNet.
        """
        synonyms = set()
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonyms.add(lemma.name().replace("_", " "))
        return synonyms

    def normalize_term(self, term):
        """
        Normalize a term using spaCy's lemmatization.
        """
        return self.nlp(term)[0].lemma_

    def extract_entities(self, user_input):
        """
        Extracts relevant entities from user input, including filters.
        """
        doc = self.nlp(user_input.lower())
        entities = {ent.text.lower() for ent in doc.ents}
        tokens = {token.text.lower() for token in doc}

        conditions = None
        for token in doc:
            if token.text in ["in", "of", "by", "with"] and token.i + 1 < len(doc):
                conditions = doc[token.i + 1].text.lower()
                break

        return entities.union(tokens), conditions

    def match_to_schema(self, entities):
        """
        Matches extracted entities to the GraphQL schema.
        """
        if not self.schema:
            return None

        schema_types = {t["name"].lower(): t for t in self.schema if t["name"]}
        possible_matches = {"resource": None, "field": None}

        for entity in entities:
            normalized_entity = self.normalize_term(entity)

            if normalized_entity in schema_types:
                possible_matches["resource"] = schema_types[normalized_entity]["name"]
                continue

            for schema_type, details in schema_types.items():
                if "fields" in details and details["fields"]:
                    field_names = {f["name"]: f for f in details["fields"]}
                    if normalized_entity in field_names:
                        possible_matches["field"] = field_names[normalized_entity]["name"]
                        break

            for synonym in self.get_synonyms(entity):
                normalized_synonym = self.normalize_term(synonym)
                if normalized_synonym in schema_types:
                    possible_matches["resource"] = schema_types[normalized_synonym]["name"]
                    break

                for schema_type, details in schema_types.items():
                    if "fields" in details and details["fields"]:
                        field_names = {f["name"]: f for f in details["fields"]}
                        if normalized_synonym in field_names:
                            possible_matches["field"] = field_names[normalized_synonym]["name"]
                            break

        return possible_matches

    def generate_query(self, intent, resource, field, condition):
        """
        Generates a GraphQL query based on intent and schema mapping.
        """
        if not resource:
            return "No valid GraphQL entities found."

        if intent == "fetch":
            query = f"""
            {{
                {resource} {{
                    {field if field else "name"}
                }}
            }}
            """
        elif intent == "filter" and field and condition:
            query = f"""
            {{
                {resource}(filter: {{ {field}: {{ eq: "{condition}" }} }}) {{
                    {field}
                }}
            }}
            """
        else:
            query = f"""
            {{
                {resource} {{
                    name
                }}
            }}
            """

        return query


# Example usage:
if __name__ == "__main__":
    gql_parser = GraphQLNLPParser("https://countries.trevorblades.com/")
    user_input = "find all countries in africa"
    extracted_entities, condition = gql_parser.extract_entities(user_input)
    schema_mapping = gql_parser.match_to_schema(extracted_entities)
    intent = "filter" if condition else "fetch"
    graphql_query = gql_parser.generate_query(intent, schema_mapping["resource"], schema_mapping["field"], condition)
    print("\nGenerated GraphQL Query:")
    print(graphql_query)
