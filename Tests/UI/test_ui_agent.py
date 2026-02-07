"""
Test Suite for Login Page with AI Self-Healing and Intent-Based Execution
Uses Pytest fixtures
"""

import pytest
import sys
import builtins

# Add project root to path
sys.path.append(builtins.PROJECT_ROOT)
from Logic.UI.Login.LoginPage import LoginPage


class TestLoginSelfHealing:
    @pytest.mark.id("UI-001")
    @pytest.mark.title("Correct Login Flow - Standard User")
    def test_login_flow_standard_user(self, ui_page, ui_context):
        ui_page.execute_by_intent(
            intent="""
            Given navigate to saucedemo.base_url page
            Given I am on the login page
            When I fill username with standard_user
            And I fill password with secret_sauce
            And I click login button
            Then I should see the inventory page
            Then Page Header should be Swag Labs

            """,
            rag_context=ui_context,
        )

    # @pytest.mark.id("UI-002")
    # @pytest.mark.title("Incorrect Login Flow - Standard User")
    # def test_login_flow_standard_user(self, ui_page, ui_context):
    #     ui_page.execute_by_intent(
    #         intent="""
    #         Given navigate to saucedemo.base_url page
    #         Given I am on the login page
    #         When I fill username with standard_user
    #         And I fill password with secret_sauce
    #         And I click login button
    #         Then I should see the inventory page
    #         Then Page Header should be Emirates Airlines
    #         """,
    #         rag_context=ui_context,
    #     )

    # @pytest.mark.id("UI-NET-002")
    # @pytest.mark.title("Validate Specific API Response")
    # def test_validate_specific_api(self, ui_page, ui_context):
    #     result = ui_page.execute_by_intent(
    #         intent="""
    #         Given I start capturing network traffic
    #         Given I am on the login page
    #         When I fill username with standard_user
    #         And I fill password with secret_sauce
    #         And I click login button
    #         Then I should see the inventory page
    #         And I Click On the burger menu on the left
    #         And I select about
    #         And get all network api calls
    #         And Check nnetwork requests for api call to '**/config*' with status 200 within the list of api calls

    #         """,
    #         rag_context=ui_context,
    #     )

    # @pytest.mark.id("UI-NET-002")
    # @pytest.mark.title("Validate Specific API Response")
    # def test_validate_specific_api(self, ui_page, ui_context):
    #     result = ui_page.execute_by_intent(
    #         intent="""
    #         Given navigate to swagger.base_url page
    #         And Check network requests for api call to '**/swagger*' with status 200 within the list of api calls
    #         """,
    #         rag_context=ui_context,
    #     )
