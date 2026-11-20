"""E2E tests for Plant Disease Detection page."""
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

BASE    = Path(__file__).resolve().parents[4] / "frontend" / "pages"
PV_COLOR= Path(__file__).resolve().parents[4] / "PlantVillage-Dataset-master" / "raw" / "color"
SESSION = '{"username":"admin","name":"Admin User","role":"admin"}'


def disease_url():
    return (BASE / "disease.html").as_uri()


def _sample_image_path():
    folder = PV_COLOR / "Tomato___healthy"
    if folder.exists():
        jpgs = sorted(folder.glob("*.jp*"))
        if jpgs:
            return str(jpgs[0])
    return None


@pytest.fixture(autouse=True)
def inject_session(page: Page):
    page.add_init_script(f"sessionStorage.setItem('agrismart_session', '{SESSION}')")


def test_disease_page_loads(page: Page):
    page.goto(disease_url())
    page.wait_for_load_state("networkidle")
    expect(page).to_have_title("Plant Disease Detection — AgriSmart AI")

def test_drop_zone_present(page: Page):
    page.goto(disease_url())
    page.wait_for_load_state("networkidle")
    expect(page.locator("#drop-zone")).to_be_visible()

def test_file_input_hidden(page: Page):
    page.goto(disease_url())
    page.wait_for_load_state("networkidle")
    # file input should be hidden (triggered by drop zone)
    inp = page.locator("#file-input")
    assert inp.count() == 1

def test_analyze_button_not_visible_before_upload(page: Page):
    page.goto(disease_url())
    page.wait_for_load_state("networkidle")
    # preview area should be hidden before upload
    expect(page.locator("#preview-area")).to_be_hidden()

def test_upload_image_shows_preview(page: Page):
    img_path = _sample_image_path()
    if img_path is None:
        pytest.skip("No PlantVillage images available")
    page.goto(disease_url())
    page.wait_for_load_state("networkidle")
    page.locator("#file-input").set_input_files(img_path)
    page.wait_for_timeout(800)
    expect(page.locator("#preview-area")).to_be_visible()
    expect(page.locator("#leaf-preview")).to_be_visible()

def test_analyze_button_appears_after_upload(page: Page):
    img_path = _sample_image_path()
    if img_path is None:
        pytest.skip("No PlantVillage images available")
    page.goto(disease_url())
    page.wait_for_load_state("networkidle")
    page.locator("#file-input").set_input_files(img_path)
    page.wait_for_timeout(800)
    expect(page.get_by_role("button", name="🔬 Analyze Leaf")).to_be_visible()

def test_result_shows_after_analyze(page: Page):
    img_path = _sample_image_path()
    if img_path is None:
        pytest.skip("No PlantVillage images available")
    page.goto(disease_url())
    page.wait_for_load_state("networkidle")
    page.locator("#file-input").set_input_files(img_path)
    page.wait_for_timeout(800)
    page.get_by_role("button", name="🔬 Analyze Leaf").click()
    page.wait_for_timeout(1500)
    result = page.locator("#result-area").inner_text()
    assert len(result) > 10
