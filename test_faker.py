from dataclasses import dataclass

import requests
from faker import Faker
from pydantic import BaseModel, Field

from test_pydantic import TokenResponseSchema

fake = Faker()



@dataclass
class Register:
    client_name: str = None
    client_email: str = None


def generate_register_user():
    yield Register(
        client_name=fake.name(),
        client_email=fake.email()
    )

class UserRegisterSchema(BaseModel):
    client_name: str = Field(..., alias='clientName')
    client_email: str = Field(..., alias='clientEmail')


def test1():
    user = next(generate_register_user())
    print(user)

def test3():
    url = 'https://simple-books-api.click/api-clients'
    user = next(generate_register_user())
    data = UserRegisterSchema(
        clientName=user.client_name,
        clientEmail=user.client_email
    )
    data = data.model_dump(by_alias=True) #превращаем данные в словарь
    response = requests.post(
        url=url,
        json=data
    )
    print(response.status_code)

    try:
        TokenResponseSchema.model_validate(response.json())
    except ValueError as e:
        raise ValueError(f'Wrong format of the body: {e}')