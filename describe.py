from pydantic import BaseModel, Field
from typing import List
import json
import yaml


def describe(model):
    schema = model.model_json_schema()
    asJson = json.dumps(schema, indent=2)
    return ("Respond with JSON that adheres to the following JSON Schema:\n" 
    +"```json\n"+ asJson + "\n```")


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