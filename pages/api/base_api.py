import requests

class BaseAPI:
    def __init__(self, base_url, auth):
        self.base_url = base_url
        self.auth = auth

    def get(self, endpoint):
        return requests.get(f"{self.base_url}{endpoint}", auth=self.auth)

    def post(self, endpoint, data):
        return requests.post(f"{self.base_url}{endpoint}", auth=self.auth, data=data)

    def put(self, endpoint, data):
        return requests.put(f"{self.base_url}{endpoint}", auth=self.auth, data=data)

    def delete(self, endpoint, params=None):
        return requests.delete(
            f"{self.base_url}{endpoint}",
            auth=self.auth,
            params=params or {"force": True}     
        )