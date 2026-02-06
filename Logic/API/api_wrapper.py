import requests
import json
import builtins
from Resources.Constants import constants, endpoints, headers
from Utils.ai_agent import AIAgent


class APIWrapper:

    def __init__(self, base_url=None):
        """
        Initialize APIWrapper.
        Responsible for creating its own AIAgent instance and passing 'self' as the wrapper.
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = 30  # Default timeout
        self.config = getattr(builtins, "CONFIG", {})
        self.agent_mode = self.config.get("agent_mode", "ENABLED")

        # Dependency Injection: Wrapper creates the Agent and passes itself
        self.ai_agent = AIAgent(api_wrapper=self)

    def initialize_api_session(self, base_url):
        self.base_url = base_url
        return self.session

    def prepare_api_request(
        self,
        base_url=None,
        endpoint=None,
        headers=None,
        request_model=None,
        test_data=None,
    ):
        url = f"{base_url or self.base_url}{endpoint}"
        request_body = test_data if test_data else {}
        return url, request_body

    def process_api_response(self, response, exp_status_code=None, exp_body=None):
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")

        if exp_status_code:
            assert (
                response.status_code == exp_status_code
            ), f"Expected status {exp_status_code}, got {response.status_code}"

        if exp_body:
            try:
                resp_json = response.json()
                for key, value in exp_body.items():
                    try:
                        assert key in resp_json, f"Key {key} not found in response"
                        assert (
                            resp_json[key] == value
                        ), f"Value mismatch for {key}: expected {value}, got {resp_json[key]}"
                    except AssertionError as e:
                        if self.agent_mode == "ENABLED":
                            print(
                                f"Standard validation failed for key '{key}': {str(e)}"
                            )
                            print("Triggering AI Agent for RESPONSE_BODY_VALIDATION...")

                            ai_result = self.ai_agent.run_agent_based_on_context(
                                context="RESPONSE_BODY_VALIDATION",
                                response=resp_json,
                                exp_response=exp_body,
                            )

                            print(f"AI Agent validation result: {ai_result}")

                            if str(ai_result).strip().lower() == "true":
                                print(
                                    "✓ Success: AI Agent validated the response body against expectations."
                                )
                                return response
                            else:
                                print(f"❌ AI Agent validation failed: {ai_result}")
                                raise Exception(
                                    f"Validation failed both normally and via AI. Last error: {str(e)}"
                                )
                        else:
                            raise e
            except json.JSONDecodeError:
                print("Failed to decode response as JSON for validation")
                pass

        return response

    def post_request_wrapper(
        self,
        endpoint,
        base_url=None,
        headers=None,
        request_body=None,
        exp_status_code=None,
        exp_body=None,
    ):
        url, body = self.prepare_api_request(
            base_url, endpoint, headers, test_data=request_body
        )

        print(f"Making POST request to: {url}")
        print(f"Headers: {headers}")
        print(f"Request Body: {body}")

        try:
            response = self.session.post(
                url, headers=headers, json=body, timeout=self.timeout, verify=False
            )
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

        return self.process_api_response(response, exp_status_code, exp_body)
