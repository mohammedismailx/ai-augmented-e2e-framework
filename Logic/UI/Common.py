from Logic.UI.BasePage import BasePage


class Common(BasePage):
    """
    Common class for shared UI logic across the application.
    Contains common locators and methods used by multiple pages.
    """

    def __init__(self, page, api_wrapper=None):
        super().__init__(page, api_wrapper)

        # Common Locators (Example)
        self.menu_button = "#react-burger-menu-btn"
        self.logout_link = "#logout_sidebar_link"
        self.shopping_cart = ".shopping_cart_link"

    def open_menu(self):
        """Open the side menu"""
        if self.is_visible(self.menu_button):
            self.click_custom(self.menu_button, "menu_button")

    def logout(self):
        """Perform logout"""
        self.open_menu()
        self.click_custom(self.logout_link, "logout_link")

    def go_to_cart(self):
        """Navigate to shopping cart"""
        self.click_custom(self.shopping_cart, "shopping_cart")
