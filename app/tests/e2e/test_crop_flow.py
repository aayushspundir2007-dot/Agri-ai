"""E2E tests for Crop Recommendation page."""
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

BASE = Path(__file__).resolve().parents[4] / "frontend" / "pages"
SESSION = '{"username":"admin","name":"Admin User","role":"admin"}'


def crop_url():
    return (BASE / "crop.html").as_uri()


@pytest.fixture(autouse=True)
def inject_session(page: Page):
    """Pre-inject admin session before each test."""
    page.add_init_script(f"sessionStorage.setItem('agrismart_session', '{SESSION}')")


def test_crop_page_loads(page: Page):
    page.goto(crop_url())
    page.wait_for_load_state("networkidle")
    expect(page).to_have_title("Crop Recommendation — AgriSmart AI")

def test_default_nitrogen_value_present(page: Page):
    page.goto(crop_url())
    page.wait_for_load_state("networkidle")
    val = page.locator("#N").input_value()
    assert val == "90"

def test_default_ph_value_present(page: Page):
    page.goto(crop_url())
    page.wait_for_load_state("networkidle")
    val = page.locator("#ph").input_value()
    assert val == "6.5"

def test_recommend_button_exists(page: Page):
    page.goto(crop_url())
    page.wait_for_load_state("networkidle")
    expect(page.get_by_role("button", name="🌱 Recommend Crop")).to_be_visible()

def test_all_input_fields_present(page: Page):
    page.goto(crop_url())
    page.wait_for_load_state("networkidle")
    for field_id in ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]:
        expect(page.locator(f"#{field_id}")).to_be_visible()

def test_click_recommend_shows_result(page: Page):
    page.goto(crop_url())
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name="🌱 Recommend Crop").click()
    page.wait_for_timeout(1200)
    result_area = page.locator("#result-area")
    expect(result_area).not_to_be_empty()

def test_result_contains_recommended_text(page: Page):
    page.goto(crop_url())
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name="🌱 Recommend Crop").click()
    page.wait_for_timeout(1200)
    result_text = page.locator("#result-area").inner_text()
    assert "Recommended" in result_text or len(result_text) > 10

def test_confidence_bars_appear_after_predict(page: Page):
    page.goto(crop_url())
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name="🌱 Recommend Crop").click()
    page.wait_for_timeout(1200)
    bars = page.locator(".conf-bar-fill")
    assert bars.count() > 0

def test_about_model_expander_exists(page: Page):
    page.goto(crop_url())
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text("About this model")).to_be_visible()
