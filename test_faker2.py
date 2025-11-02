from dataclasses import dataclass
import allure
import json

import pytest
import requests
from faker import Faker
from pydantic import Field, BaseModel

fake = Faker()

@dataclass #создает класс для хранения данных клиент_имя и клиент_почта
class Register:
    client_name: str
    client_email: str

@pytest.fixture(scope="module")
def get_user():
    return Register(
        client_name=fake.name(),
        client_email=fake.email()
    )

class UserRequestSchema(BaseModel):
    client_name: str = Field(..., alias='clientName')
    client_email: str = Field(..., alias='clientEmail')

class TokenSchema(BaseModel):
    access_token: str = Field(..., alias='accessToken')

@pytest.fixture(scope='module')
def initial_token(get_user):
    url = 'https://simple-books-api.click/api-clients'
    data = UserRequestSchema(
        clientName=get_user.client_name,
        clientEmail=get_user.client_email
    )
    data = data.model_dump(by_alias=True)
    response = requests.post(
        url=url,
        json=data
    )
    print(response.status_code)
    print(data['clientName'])

    TokenSchema.model_validate(response.json())

    return response.json()['accessToken'], data

# @dataclass
# class Order:
#     book_id: int
#     customer_name: str

# @pytest.fixture(scope="session")
# def gen_order():
#     return Order(
#         book_id=1,
#         customer_name=fake.name()
#     )

class OrderSchema(BaseModel):
    book_id: int = Field(..., alias='bookId')
    customerName: str = Field(..., alias='customerName')

class OrderSchemaResponse(BaseModel):
    created: bool
    order_id: str = Field(..., alias='orderId')



@pytest.fixture(scope='module')
def order_id(initial_token):
    url = 'https://simple-books-api.click/orders'
    token, first_client_name = initial_token
    data = OrderSchema(
        bookId=1,
        customerName=first_client_name['clientName']
    )
    data = data.model_dump(by_alias=True)
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.post(
        url=url,
        json=data,
        headers=headers
    )
    print(response.status_code)

    OrderSchemaResponse.model_validate(response.json())

    return response.json()['orderId']

@allure.story('Created order')
def test2(order_id):
    with allure.step('Checking that order_id isn\'t None'):
        assert order_id is not None
        print(order_id)


class GetOrderSchema(BaseModel):
    id: str
    book_id: int = Field(..., alias='bookId')
    customer_name: str = Field(..., alias='customerName')
    quantity: int
    timestamp: int

@allure.story('Getting an order')
def test3(order_id, initial_token):
    token, first_client_name = initial_token
    url = f'https://simple-books-api.click/orders/{order_id}'

    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(
        url=url,
        headers=headers
    )

    allure.attach(
        body=json.dumps(response.json(), indent=2),
        name='GET Order Response',
        attachment_type=allure.attachment_type.JSON
    )

    GetOrderSchema.model_validate(response.json())
    print('Get order schema is correct')

    with allure.step('Checking that we can get the order we created'):
        assert response.status_code == 200
        print('Status code is correct')
        print(response.json()['customerName'])

        allure.attach(
            body=response.json()['customerName'],
            name='Getting created customer\'s name',
            attachment_type=allure.attachment_type.TEXT
        )

@dataclass
class Customer:
    customer_name: str

@pytest.fixture(scope='session')
def gen_customer2():
    return Customer (
        customer_name=fake.name()
    )

class CustomerSchema(BaseModel):
    customer_name: str = Field(..., alias='customerName')

@pytest.fixture
def changed_name(order_id, initial_token, gen_customer2):
    token, first_client_name = initial_token
    url = f'https://simple-books-api.click/orders/{order_id}'

    headers = {
        'Authorization': f'Bearer {token}'
    }
    data1 = CustomerSchema(
        customerName=gen_customer2.customer_name,
    )
    data = data1.model_dump(by_alias=True)
    response = requests.patch(
        url=url,
        headers=headers,
        json=data
    )
    print(response.status_code)
    print(data1)
    return response, data1

@allure.story('Changing name')
def test4(changed_name):
    response, data1  = changed_name
    with allure.step('Sending a request for a name change'):
        assert response.status_code == 204
        print('Status code is correct')

@pytest.fixture
def book_id_and_changed_name(changed_name, order_id, initial_token):
    token, first_client_name = initial_token
    url = f'https://simple-books-api.click/orders/{order_id}'

    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(
        url=url,
        headers=headers
    )

    GetOrderSchema.model_validate(response.json())
    print('Get order schema is correct')

    return response

@allure.story('Getting the order with a new name')
def test5(book_id_and_changed_name, changed_name):
    response, data1 = changed_name

    customer_name2 = book_id_and_changed_name.json()['customerName']

    with allure.step('Making sure the new name exists'):
        assert book_id_and_changed_name.status_code == 200
        print('Status code is correct')

    with allure.step('Making sure the new name is the we created earlier'):
        assert customer_name2 == data1.customer_name
        print(customer_name2)
        print('Username changed')


class DeleteBodySchema(BaseModel):
    book_id: int = Field(..., alias='bookId')
    customer_name: str = Field(..., alias='customerName')


@pytest.fixture
def deleted(book_id_and_changed_name, order_id, initial_token):
    token, first_client_name = initial_token
    url = f'https://simple-books-api.click/orders/{order_id}'

    headers = {
        'Authorization': f'Bearer {token}'
    }

    book_id3 = book_id_and_changed_name.json()['bookId']
    customer_name3 = book_id_and_changed_name.json()['customerName']

    data = DeleteBodySchema (
        bookId=book_id3,
        customerName=customer_name3
    )

    data = data.model_dump(by_alias=True)

    response = requests.delete(
        url=url,
        headers=headers,
        json=data
    )

    return response

@allure.story('Deleting the order')
def test6_and_7(deleted, order_id, initial_token):
    token, first_client_name = initial_token
    with allure.step('Deleting the order'):
        assert deleted.status_code == 204
        print('Item has been deleted')

    url = f'https://simple-books-api.click/orders/{order_id}'

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(
        url=url,
        headers=headers
    )
    with allure.step('Verifying that the order does not exist'):
        assert response.status_code == 404
        print('Item not found')
