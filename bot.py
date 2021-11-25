import os

from dotenv import load_dotenv

from store_requests import (add_product_to_cart, create_token,
                            get_all_products, get_cart)


def main():
    load_dotenv()
    token = create_token(os.environ['MOLTIN_CLIENT_ID'])
    print(get_cart(token, 123))


if __name__ == '__main__':
    main()
