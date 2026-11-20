"""E2E tests for login flow via HTML frontend."""
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

BASE = Path(__file__).resolve().parents[4] / "frontend" / "pages"


@pytest.fixture(scope="module")
def browser_context(playwright_instance):
    browser = playwright_instance.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    yield ctx
    browser.close()


def login_url():
    return (BASE / "login.html").as_uri()

def overview_url():
    return (BASE / "overview.html").as_uri()


def test_login_page_loads(page: Page):
    page.goto(login_url())
    expect(page).to_have_title("Sign In — AgriSmart AI")

def test_login_form_has_username_field(page: Page):
    page.goto(login_url())
    expect(page.locator("#username")).to_be_visible()

def test_login_form_has_password_field(page: Page):
    page.goto(login_url())
    expect(page.locator("#password")).to_be_visible()

def test_login_form_has_submit_button(page: Page):
    page.goto(login_url())
    expect(page.get_by_role("button", name="Sign In →")).to_be_visible()

def test_empty_form_shows_error(page: Page):
    page.goto(login_url())
    page.get_by_role("button", name="Sign In →").click()
    page.wait_for_timeout(800)
    err = page.locator("#login-error")
    expect(err).to_be_visible()

def test_wrong_password_shows_error(page: Page):
    page.goto(login_url())
    page.fill("#username", "admin")
    page.fill("#password", "wrongpassword")
    page.get_by_role("button", name="Sign In →").click()
    page.wait_for_timeout(1500)
    expect(page.locator("#login-error")).to_be_visible()

def test_valid_login_redirects_to_overview(page: Page):
    page.goto(login_url())
    page.fill("#username", "admin")
    page.fill("#password", "admin123")
    page.get_by_role("button", name="Sign In →").click()
    page.wait_for_url("**/overview.html", timeout=5000)
    expect(page).to_have_title("Overview — AgriSmart AI")

def test_logout_returns_to_login(page: Page):
    # first log in
    page.goto(login_url())
    page.fill("#username", "admin")
    page.fill("#password", "admin123")
    page.get_by_role("button", name="Sign In →").click()
    page.wait_for_url("**/overview.html", timeout=5000)
    # click logout
    page.get_by_role("button", name="Sign Out").click()
    page.wait_for_url("**/login.html", timeout=5000)
    expect(page).to_have_title("Sign In — AgriSmart AI")

def test_admin_can_see_user_management(page: Page):
    page.goto(login_url())
    page.fill("#username", "admin")
    page.fill("#password", "admin123")
    page.get_by_role("button", name="Sign In →").click()
    page.wait_for_url("**/overview.html", timeout=5000)
    expect(page.get_by_text("User Management")).to_be_visible()

def test_viewer_cannot_see_user_management(page: Page):
    page.goto(login_url())
    page.fill("#username", "farmer")
    page.fill("#password", "farmer123")
    page.get_by_role("button", name="Sign In →").click()
    page.wait_for_url("**/overview.html", timeout=5000)
    expect(page.locator("[data-page='user-management']")).to_be_hidden()
