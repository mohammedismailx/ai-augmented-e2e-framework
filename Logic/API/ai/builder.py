from Resources.Constants import endpoints, headers
from Utils.utils import load_test_data
from Utils.logger import FrameworkLogger as log


class AIAgentBuilder:
    def __init__(self, api_wrapper):
        self.api_wrapper = api_wrapper

    def communicate_with_agent(
        self, agent_type, scenario, override_test_data=None, base_url=None
    ):
        """
        Send a request to the AI Agent and return the response.
        Mimics 'Communicate With Agent' keyword.
        """
        if agent_type == "LOCAL":
            # Define paths and version (conceptually)
            # local_request_model = ...
            # local_response_model = ...
            # local_test_data = ...
            version = "v1"

            # Use override test data if provided
            test_data_to_use = (
                override_test_data
                if override_test_data
                else load_test_data("LocalModel")
            )

            log.safe_print(f"Making AI Agent request with scenario: {scenario}")
            # print(f"Using test data: {test_data_to_use}")

            # Extract payload from test data structure
            # Assuming the structure matches what we've seen: success -> input -> body
            try:
                payload = test_data_to_use[scenario]["input"]["body"]
            except KeyError:
                log.safe_print(f"Scenario {scenario} not found in test data")
                return None

            # Make the API call
            response = self.api_wrapper.post_request_wrapper(
                base_url=base_url,
                endpoint=endpoints.CHAT_COMPLETION,
                # version=version, # APIWrapper doesn't handle versioning explicitly yet, usually part of URL
                headers=headers.WITHOUT_TOKEN_HEADERS,  # Using constant from headers.py
                request_body=payload,
                # schema_validation=False,
                # body_validation=False,
                # timeout=4000
            )

            if response:
                log.safe_print(
                    f"AI Agent response received with status: {response.status_code}"
                )
            return response

        elif agent_type == "GITLAB_DUO":
            version = "v4"

            test_data_to_use = (
                override_test_data
                if override_test_data
                else load_test_data("GitlabDuo")
            )

            log.safe_print(f"Making AI Agent request with scenario: {scenario}")

            try:
                payload = test_data_to_use[scenario]["input"]["body"]
            except KeyError:
                log.safe_print(f"Scenario {scenario} not found in test data")
                return None

            response = self.api_wrapper.post_request_wrapper(
                base_url=base_url,  # Should be GITLAB_DUO_BASE_URL
                endpoint=endpoints.CODE_SUGGESTIONS,
                headers=headers.GITLAB_DUO_HEADERS,
                request_body=payload,
            )
            log.safe_print(f"Response IS __________________________ {response}")
            if response:
                log.safe_print(
                    f"AI Agent response received with status: {response.status_code}"
                )
            return response

        return None
