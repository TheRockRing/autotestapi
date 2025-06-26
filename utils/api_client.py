import requests

class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def get(self, endpoint):
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url)
        return response

    def get_with_auth(self, endpoint):
        url = f"{self.base_url}{endpoint}"

        with open("token.txt", "r") as f:
            token = f.read().strip()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        return response

    def post_with_auth(self, endpoint, payload):
        url = f"{self.base_url}{endpoint}"

        with open("token.txt", "r") as f:
            token = f.read().strip()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers)
        return response

    def post(self, endpoint, payload):
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, json=payload)
        return response

    def post_header(self, endpoint, headers):
        url = f"{self.base_url}{endpoint}"
        response = requests.post(
            url,
            headers=headers,
            verify=False)  # убрать, если нужен сертификат
        return response

    def post(self, endpoint, payload):
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, json=payload)
        return response

    def get(self, endpoint):
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url)
        return response