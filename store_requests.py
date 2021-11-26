import requests

def create_token(client_id):

    data = {
        'client_id': client_id,
        'grant_type': 'implicit'
    }

    response = requests.post('https://api.moltin.com/oauth/access_token', data=data)
    response.raise_for_status()

    return response.json()['access_token']


def get_all_products(token):

    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get('https://api.moltin.com/v2/products', headers=headers)
    response.raise_for_status()

    return response.json()


def get_product(token, product_id):

    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/products/{product_id}', headers=headers)
    response.raise_for_status()

    return response.json()


def get_product_image(token, image_id):

    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/files/{image_id}', headers=headers)
    response.raise_for_status()

    return response.json()


def add_product_to_cart(token, cart_id, product_id, quantity=1):

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = {
        "data": {
            "id": product_id,
            "type": "cart_item",
            "quantity": quantity,
        }
    }

    response = requests.post(f'https://api.moltin.com/v2/carts/{cart_id}/items', headers=headers, json=data)
    response.raise_for_status()

    return response.json()


def delete_product_from_cart(token, cart_id, product_id):

    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.delete(f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}', headers=headers)
    response.raise_for_status()

    return response.json()


def get_cart(token, cart_id):

    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/carts/{cart_id}/items', headers=headers)
    response.raise_for_status()

    return response.json()


def create_customer(token, email, chat_id):

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = {
        "data": {
            "type": "customer",
            "name": str(chat_id),
            "email": email,
        }
    }

    response = requests.post(f'https://api.moltin.com/v2/customers', headers=headers, json=data)
    response.raise_for_status()

    return response.json()


def get_customer(token, customer_id):

    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get(f'https://api.moltin.com/v2/customers/{customer_id}', headers=headers)
    response.raise_for_status()

    return response.json()