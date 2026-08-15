from pages.api.base_api import BaseAPI

class PostsAPI(BaseAPI):
    ENDPOINT = "/posts"

    def get_all_posts(self):
        return self.get(self.ENDPOINT)

    def get_post(self, post_id):
        return self.get(f"{self.ENDPOINT}/{post_id}")

    def create_post(self, title, content, status="draft"):
        return self.post(self.ENDPOINT, {
            "title": title,
            "content": content,
            "status": status
        })

    def update_post(self, post_id, **fields):
        return self.put(f"{self.ENDPOINT}/{post_id}", fields)

    def find_post_by_title(self, title):
        response = self.get_all_posts()
        posts = response.json()
        for post in posts:
            if post['title']['rendered'] == title:
                return post
        return None

    def delete_post(self, post_id):
        return self.delete(f"{self.ENDPOINT}/{post_id}")