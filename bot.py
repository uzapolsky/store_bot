import os

from dotenv import load_dotenv

from store_requests import create_token, get_all_products


def main():
    load_dotenv()
    token = create_token(os.environ['MOLTIN_CLIENT_ID'])
    print(get_all_products(token))


if __name__ == '__main__':
    main()
