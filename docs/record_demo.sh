#!/usr/bin/env bash
# Runs all agents in MOCK_LLM mode — no OpenAI API key required.
# Used by the demo-gif CI workflow to generate docs/demo.gif

set -e
export MOCK_LLM=true

echo "╔══════════════════════════════════════════╗"
echo "║       AI QA Toolbox — Live Demo          ║"
echo "╚══════════════════════════════════════════╝"
echo ""
sleep 0.5

echo "┌─ Step 1: Log Classifier Agent ───────────"
echo "  Reads a Playwright failure log and classifies"
echo "  the root cause using an LLM."
echo ""
sleep 0.5
python agents/log_classifier/main.py
echo ""
sleep 1

echo "┌─ Step 2: Selector Healer Agent ──────────"
echo "  Takes broken CSS/XPath locators and suggests"
echo "  robust Playwright-native replacements."
echo ""
sleep 0.5
python agents/selector_healer/main.py
echo ""
sleep 1

echo "┌─ Step 3: UI Auditor CLI ──────────────────"
echo "  Captures a screenshot and runs a vision LLM"
echo "  UX audit. (Screenshot capture skipped in mock mode)"
echo ""
sleep 0.5
python agentic-ui-auditor/auditor.py --url https://example.com
echo ""
sleep 0.5

echo "╔══════════════════════════════════════════╗"
echo "║           Demo complete ✓                ║"
echo "╚══════════════════════════════════════════╝"
