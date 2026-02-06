from Logic.UI.Common import Common


class LoginPage(Common):
    """Page Object for SauceDemo Login Page"""

    def __init__(self, page, api_wrapper=None):
        super().__init__(page, api_wrapper)
        
        # Locators
        self.username_input = "#user-name"
        self.password_input = "#password"
        self.login_button = "#login-button"
        self.error_message = "[data-test='error']"

        # Incorrect locator for testing self-healing
        self.incorrect_login_button = "#wrong-login-button-id"
        self.incorrect_add_to_cart_button = "#incorrect_add_to_cart_button"

    def login(self, username, password):
        """Perform login with username and password"""
        print(f"Logging in with username: {username}")

        # Fill username
        self.fill_input(self.username_input, username)

        # Fill password
        self.fill_input(self.password_input, password)

        # Click login button
        self.click_custom(self.login_button, "login_button")

        # Wait for navigation
        self.page.wait_for_load_state("networkidle")
        print("Login completed")

    def get_error_message(self):
        """Get error message if login fails"""
        if self.is_visible(self.error_message):
            return self.get_text(self.error_message)
        return None

    def is_logged_in(self):
        """Check if user is logged in by verifying URL"""
        return "inventory" in self.get_url()

    def click_login_with_incorrect_locator(self):
        """Test method to trigger self-healing with incorrect locator"""
        print("Testing self-healing with incorrect locator...")
        return self.click_custom(self.incorrect_login_button, "Login_input_locator")
