import json

from ai_qa_toolbox.core.llm.client import ask_llm


BROKEN_SELECTORS = [
    {
        "locator": "#checkout-submit-btn",
        "context": "Submit button on the checkout page",
        "error": "TimeoutError: Timeout 30000ms exceeded waiting for locator('#checkout-submit-btn')",
    },
    {
        "locator": "//button[contains(@class, 'btn-primary')]",
        "context": "Primary action button on the login form",
        "error": 'Error: strict mode violation: locator(\'//button[contains(@class, "btn-primary")]\') resolved to 3 elements',
    },
    {
        "locator": ".payment-panel > .pay-now-cta",
        "context": "Pay Now CTA inside the payment panel",
        "error": "Error: Element is not visible: .payment-panel > .pay-now-cta",
    },
]


def main():
    for index, selector in enumerate(BROKEN_SELECTORS):
        locator = selector["locator"]
        context = selector["context"]
        error = selector["error"]

        prompt = f"""
You are an expert in Playwright test automation and CSS selectors.

A test is failing because this locator is broken:
  Locator: {locator}
  Element context: {context}
  Error: {error}

Suggest a fix by responding with ONLY a valid JSON object \u2014 no markdown, no explanation, no code fences.

The JSON must have exactly these fields:
- "original_locator": the failing locator string
- "suggested_css": a more robust CSS selector for this element
- "suggested_playwright": the best Playwright-native locator (using getByRole, getByText, getByLabel, or getByTestId)
- "reason_original_failed": one sentence explaining why the original locator broke
- "confidence": one of [high, medium, low]
"""

        result = ask_llm(prompt)

        if index > 0:
            print()
        print(f"=== SELECTOR HEALER: {locator} ===")
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            print(result)
        else:
            print(json.dumps(parsed, indent=2))


if __name__ == "__main__":
    main()
