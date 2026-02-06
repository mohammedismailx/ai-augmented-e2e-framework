import builtins
from Resources.Constants import endpoints, headers
from Utils.utils import load_test_data
from Logic.API.api_wrapper import APIWrapper


class PostsController:
    def __init__(self, api_wrapper=None):
        # Initialize internal wrapper if not provided
        self.base_url = getattr(builtins, "URLS", {}).get("api", {})["base_url"]
        self.api_wrapper = api_wrapper if api_wrapper else APIWrapper(self.base_url)

    def createPosts(self, scenario="success", override_test_data=None, base_url=None):
        """
        Send a request to the AI Agent and return the response.
        Mimics 'Communicate With Agent' keyword.
        """
        # Use override test data if provided
        test_data_to_use = (
            override_test_data
            if override_test_data
            else load_test_data("../PostsService/PostsController/createPosts")
        )

        # Extract payload from test data structure
        try:
            payload = test_data_to_use[scenario]["input"]["body"]
        except KeyError:
            print(f"Scenario {scenario} not found in test data")
            return None

        # Extract expected results
        expected_results = test_data_to_use[scenario].get("output", {})
        exp_status_code = expected_results.get("status_code")
        exp_body = expected_results.get("body")

        # Make the API call
        response = self.api_wrapper.post_request_wrapper(
            base_url=base_url,
            endpoint=endpoints.ADD_POSTS,
            headers=headers.WITHOUT_TOKEN_HEADERS,
            request_body=payload,
            exp_status_code=exp_status_code,
            exp_body=exp_body,
        )
        print(f"Response Status Code: {response.status_code}")
        try:
            print(f"Response Body: {response.json()}")
        except:
            print(f"Response Body: {response.text}")

        return response
