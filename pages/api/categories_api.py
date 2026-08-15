from pages.api.base_api import BaseAPI

class CategoriesAPI(BaseAPI):
    ENDPOINT = "/categories"

    def get_all_categories(self):
        return self.get(self.ENDPOINT)

    def get_category(self, category_id):
        return self.get(f"{self.ENDPOINT}/{category_id}")

    def create_category(self, name, description="", parent=None):
        payload = {
            "name": name,
            "description": description
        }
        if parent is not None:
            payload["parent"] = parent
        return self.post(self.ENDPOINT, payload)

    def delete_category(self, category_id):
        return self.delete(f"{self.ENDPOINT}/{category_id}")