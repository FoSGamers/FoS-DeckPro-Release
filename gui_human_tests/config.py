#!/usr/bin/env python3
"""
Configuration for FoS_DeckPro GUI Human Testing Suite
"""

# OpenAI Vision API Configuration
OPENAI_MODEL = "gpt-4o"  # Use gpt-4o for best vision analysis
OPENAI_MAX_TOKENS = 2000
OPENAI_TEMPERATURE = 0.3  # Lower temperature for more consistent analysis

# Test Configuration
SCREENSHOT_DELAY = 0.5  # Seconds to wait after taking screenshot
API_RATE_LIMIT_DELAY = 1.0  # Seconds between API calls
TEST_TIMEOUT = 300  # Seconds before test timeout

# Screenshot Quality
SCREENSHOT_FORMAT = "PNG"
SCREENSHOT_QUALITY = 95

# Analysis Configuration
ANALYSIS_PROMPT_TEMPLATE = """
Analyze this screenshot of a Magic: The Gathering card inventory management application called FoS_DeckPro.

Context: {context}

Please provide a detailed analysis covering:

1. **Visual Design & Layout:**
   - Is the interface clean, modern, and professional?
   - Are elements properly aligned and spaced?
   - Is the color scheme appropriate and accessible?
   - Are fonts readable and consistent?

2. **User Experience:**
   - Is the interface intuitive and easy to navigate?
   - Are buttons, menus, and controls clearly visible and accessible?
   - Is the information hierarchy clear and logical?
   - Would a human user understand what to do next?

3. **Functionality Assessment:**
   - What appears to be happening in this screenshot?
   - Are there any visible errors, warnings, or issues?
   - Is the current state of the application clear to the user?
   - Are there any missing elements or broken functionality?

4. **Human-Centered Design:**
   - Does this interface feel welcoming and user-friendly?
   - Would different types of users (beginner, power user, etc.) find this usable?
   - Are there any accessibility concerns?
   - Does the interface follow modern UI/UX best practices?

5. **Specific Issues:**
   - List any errors, warnings, or problematic elements
   - Identify any confusing or unclear interface elements
   - Note any missing functionality or broken features

6. **Overall Assessment:**
   - Rate the overall quality (1-10)
   - Provide specific recommendations for improvement
   - Would you recommend this interface to users?

Provide your analysis in a structured, detailed format with specific observations and actionable feedback.
"""

# Persona-specific analysis prompts
PERSONA_ANALYSIS_PROMPTS = {
    "normal_user": "Focus on typical user workflow and ease of use.",
    "dumb_user": "Look for confusing elements, unclear instructions, and potential user errors.",
    "breaker_user": "Identify security issues, error handling, and crash prevention.",
    "power_user": "Assess efficiency, shortcuts, and advanced features.",
    "accessibility_user": "Focus on keyboard navigation, screen reader compatibility, and accessibility features.",
    "curiosity_user": "Evaluate discoverability, help systems, and user guidance.",
    "regression_user": "Check for consistency, data integrity, and state management."
}

# Report Configuration
REPORT_TEMPLATE = """
# FoS_DeckPro GUI Analysis Report
Generated: {timestamp}

## Summary
- Total screenshots analyzed: {total_screenshots}
- Successful analyses: {successful_analyses}
- Failed analyses: {failed_analyses}
- Overall quality score: {average_score}/10

## Key Findings
{key_findings}

## Recommendations
{recommendations}

## Detailed Analyses
{detailed_analyses}
"""

# File paths and directories
SCREENSHOTS_BASE_DIR = "screenshots"
REPORTS_DIR = "reports"
LOGS_DIR = "logs"

# Ensure directories exist
import os
for directory in [SCREENSHOTS_BASE_DIR, REPORTS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True) 