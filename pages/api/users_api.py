from pages.api.base_api import BaseAPI

class UsersAPI(BaseAPI):
    ENDPOINT = "/users"

    def get_all_users(self):
        return self.get(self.ENDPOINT)

    def get_user(self, user_id):
        return self.get(f"{self.ENDPOINT}/{user_id}")

    def get_current_user(self):
        return self.get(f"{self.ENDPOINT}/me")

    def create_user(self, username, email, password, role="subscriber"):
        return self.post(self.ENDPOINT ,{
            "username": username,
            "email": email,
            "password": password,
            "roles": [role]
        })

    def delete_user(self, user_id, reassign_id=1):
        return self.delete(f"{self.ENDPOINT}/{user_id}", params={"force": True, "reassign": reassign_id})