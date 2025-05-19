# Example: nested types
from dataclasses import dataclass
from typing import Literal
from castfit import castfit


@dataclass
class Pet:
    name: str
    type: Literal["cat", "dog", "other"]
    age: int


@dataclass
class Owner:
    name: str
    pets: list[Pet]


owner_data = {
    "name": "Alice",
    "pets": [
        {"name": "Cuddles", "type": "cat", "age": "4"},
        {"name": "Buddy", "type": "dog", "age": "2.5"},  # age will be cast to int(2)
    ],
}

owner = castfit(Owner, owner_data)

assert owner.name == "Alice"
assert len(owner.pets) == 2
assert isinstance(owner.pets[0], Pet)
assert owner.pets[0].name == "Cuddles"
assert owner.pets[0].type == "cat"
assert owner.pets[0].age == 4
assert owner.pets[1].name == "Buddy"
assert owner.pets[1].age == 2  # Cast from "2.5" to int
