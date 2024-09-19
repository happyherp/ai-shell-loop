from pydantic import BaseModel, Field
from typing import List
import json
from .util import codeblock

def describe(model):
    schema = model.model_json_schema()
    as_json = json.dumps(schema, indent=0)
    return codeblock(as_json)


if __name__ == "__main__":

    class Address(BaseModel):
        street: str = Field(..., description="The street name and number")
        city: str = Field(..., title=None, description="The city")
        state: str
        zip: str

    class Person(BaseModel):
        name: str
        age: int
        addresses: List[Address]

    print(describe(Person))