"""
Test Suite for Login Page with AI Self-Healing
Uses Pytest fixtures
"""

import sys
import builtins

# Add project root to path
sys.path.append(builtins.PROJECT_ROOT)
from Logic.UI.Login.LoginPage import LoginPage


class TestLoginSelfHealing:
    """Test suite for Login Page with AI Self-Healing"""

    def test_inventory_self_healing(self, page):
        """
        Test AI Agent self-healing functionality on the inventory page.
        """
        # Initialize LoginPage (config loaded from globals)
        login_page = LoginPage(page)

        # Navigate to SauceDemo inventory using the urls fixture
        # We are already logged in via auth_state fixture in conftest.py
        login_page.navigate(builtins.URLS["saucedemo"]["inventory_url"])

        # Trigger self-healing with incorrect locator for 'Add to Cart' button
        # The AI should find the first 'Add to Cart' button (.btn_inventory)
        result = login_page.click_custom("#wrong-add-to-cart-id", "add_to_cart_button")

        # Verify result
        assert result == "PASS", f"Expected PASS but got {result}"
        print("✓ Inventory self-healing test passed")
