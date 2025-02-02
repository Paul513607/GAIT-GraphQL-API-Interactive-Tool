from pydantic import BaseModel
from typing import List

class Api(BaseModel):
    name: str
    url: str

apis = [
    {
        "name": "Countries API",
        "url": "https://countries.trevorblades.com/",
    },
    {
        "name": "EHRI",
        "url": "https://portal.ehri-project.eu/api/graphql",
    },
    {
        "name": "TCGdex",
        "url": "https://api.tcgdex.net/v2/graphql",
    },
]