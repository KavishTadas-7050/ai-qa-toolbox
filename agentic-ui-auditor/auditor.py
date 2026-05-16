import argparse
import json
import sys
from pathlib import Path
from ai_qa_toolbox.ui_auditor.screenshot import take_screenshot
from ai_qa_toolbox.core.llm.client import ask_llm_with_image


DEFAULT_URL = "https://example.com"
SCREENSHOT_PATH = Path("audit_screenshot.png")

AUDIT_PROMPT = """
  You are a senior UX and accessibility expert performing a UI audit.
  Analyze the provided screenshot and identify UX issues.

  Respond ONLY with a valid JSON array — no markdown, no explanation, no code fences.
  Each element in the array must be an object with exactly these fields:
  - "issue": short description of the problem found
  - "category": one of [spacing, color_contrast, text_legibility, layout, accessibility, navigation, other]
  - "severity": one of [High, Medium, Low]
  - "location": where on the screen the issue is (e.g. "top navigation", "hero section", "footer")
  - "recommendation": one concrete actionable fix

  If no issues are found, return an empty array: []
  """


def capture(url: str) -> bytes:
    """Capture screenshot of url, return raw bytes. Skips browser in mock mode."""
    import os
    if os.getenv("MOCK_LLM") == "true":
        # Minimal valid 1x1 PNG — no browser needed in mock/demo mode
        import base64
        _TINY_PNG = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
            b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
            b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        return _TINY_PNG
    take_screenshot(url, SCREENSHOT_PATH)
    return SCREENSHOT_PATH.read_bytes()


def analyze(image_bytes: bytes) -> list[dict]:
    """Send screenshot to vision LLM, parse and return list of issues."""
    raw = ask_llm_with_image(AUDIT_PROMPT, image_bytes)
    try:
        result = json.loads(raw)
        if not isinstance(result, list):
            result = [result]
        return result
    except json.JSONDecodeError:
        return [{"issue": "Failed to parse LLM response", "raw": raw,
                 "category": "other", "severity": "Low",
                 "location": "N/A", "recommendation": "Check LLM prompt"}]


def print_report(url: str, issues: list[dict]) -> None:
    """Print a human-readable audit report to stdout."""
    print("=" * 60)
    print("UI AUDIT REPORT")
    print(f"URL: {url}")
    print(f"Issues found: {len(issues)}")
    print("=" * 60)
    if not issues:
        print("No UX issues detected.")
        return
    for i, issue in enumerate(issues, 1):
        print(f"\n[{i}] {issue.get('severity', '?').upper()} — {issue.get('category', '?')}")
        print(f"    Issue:          {issue.get('issue', '')}")
        print(f"    Location:       {issue.get('location', '')}")
        print(f"    Recommendation: {issue.get('recommendation', '')}")
    print("\n" + "=" * 60)


def main(url: str = DEFAULT_URL) -> list[dict]:
    print(f"[1/3] Capturing screenshot of {url} ...")
    image_bytes = capture(url)
    print(f"[2/3] Sending to vision LLM for UX analysis ...")
    issues = analyze(image_bytes)
    print(f"[3/3] Generating report ...")
    print_report(url, issues)
    return issues


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-powered UI auditor")
    parser.add_argument("--url", default=DEFAULT_URL, help="URL to audit")
    args = parser.parse_args()
    main(args.url)
