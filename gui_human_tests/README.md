# FoS_DeckPro GUI Human Testing Suite

A comprehensive, APTPT/REI/HCE-compliant GUI testing suite that simulates real human users interacting with the FoS_DeckPro Magic: The Gathering card inventory management application.

## Overview

This testing suite provides **world-class, human-like, adversarial, and exploratory GUI testing** that ensures your app looks, feels, and works exactly as intended for all types of users.

### Features

- **7 Human Personas**: Normal, Dumb, Breaker, Power, Accessibility, Curiosity, and Regression users
- **PyAutoGUI Automation**: Real mouse/keyboard simulation with screenshots
- **OpenAI Vision Integration**: AI-powered UI/UX analysis and feedback
- **Comprehensive Reporting**: Detailed reports with visual evidence
- **APTPT/REI/HCE Compliance**: Robust, convergent, and adaptive testing

## Setup

### 1. Install Dependencies

```bash
pip install pyautogui pillow openai
```

### 2. Set OpenAI API Key (Optional but Recommended)

For AI-powered screenshot analysis:

```bash
export OPENAI_API_KEY='your-openai-api-key-here'
```

Or add to your shell profile:
```bash
echo 'export OPENAI_API_KEY="your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### 3. Verify Installation

```bash
cd gui_human_tests
python3 -c "import pyautogui, openai; print('✅ Dependencies installed successfully')"
```

## Usage

### Run All Tests with Vision Analysis

```bash
cd gui_human_tests
python3 run_all_gui_human_tests.py
```

This will:
1. Run all 7 persona tests
2. Take screenshots of every action
3. Analyze screenshots with OpenAI Vision (if API key provided)
4. Generate comprehensive reports

### Run Individual Persona Tests

```bash
# Normal user workflow
python3 test_normal_user.py

# Dumb user (random clicks, confusion)
python3 test_dumb_user.py

# Breaker user (trying to break the app)
python3 test_breaker_user.py

# Power user (shortcuts, efficiency)
python3 test_power_user.py

# Accessibility user (keyboard navigation)
python3 test_accessibility_user.py

# Curiosity user (explores everything)
python3 test_curiosity_user.py

# Regression user (consistency testing)
python3 test_regression_user.py
```

### Run Vision Analysis Only

```bash
python3 vision_analyzer.py
```

## Persona Descriptions

### 1. Normal User
- **Behavior**: Typical workflow, adds cards, saves inventory
- **Focus**: Ease of use, intuitive navigation
- **Tests**: File menu, add card dialog, save functionality

### 2. Dumb User
- **Behavior**: Random clicks, typos, closes dialogs unexpectedly
- **Focus**: Error handling, user guidance, crash prevention
- **Tests**: Random interactions, invalid input, dialog management

### 3. Breaker User
- **Behavior**: Rapid actions, invalid data, tries to break everything
- **Focus**: Security, error handling, data integrity
- **Tests**: Double-clicks, invalid input, mass delete, undo/redo spam

### 4. Power User
- **Behavior**: Keyboard shortcuts, bulk actions, efficiency
- **Focus**: Advanced features, shortcuts, performance
- **Tests**: Cmd+N, Cmd+S, Cmd+Z, bulk operations

### 5. Accessibility User
- **Behavior**: Keyboard-only navigation, tab order, accessibility
- **Focus**: Accessibility, keyboard navigation, screen reader support
- **Tests**: Tab navigation, keyboard shortcuts, accessibility features

### 6. Curiosity User
- **Behavior**: Explores every menu, button, and dialog
- **Focus**: Discoverability, help systems, user guidance
- **Tests**: Menu exploration, dialog opening, feature discovery

### 7. Regression User
- **Behavior**: Repeats actions, tests consistency, undo/redo
- **Focus**: Data integrity, state management, consistency
- **Tests**: Add/undo/redo cycles, save/load, repeat actions

## Output Files

After running tests, you'll find:

### Screenshots
- `screenshots_normal_user/` - Normal user workflow screenshots
- `screenshots_dumb_user/` - Random interaction screenshots
- `screenshots_breaker_user/` - Break attempt screenshots
- `screenshots_power_user/` - Power user action screenshots
- `screenshots_accessibility_user/` - Keyboard navigation screenshots
- `screenshots_curiosity_user/` - Exploration screenshots
- `screenshots_regression_user/` - Consistency test screenshots

### Reports
- `comprehensive_test_report_YYYYMMDD_HHMMSS.md` - Final test summary
- `vision_analysis_report_YYYYMMDD_HHMMSS.md` - AI analysis report (if API key provided)
- `vision_analysis_results_YYYYMMDD_HHMMSS.json` - Raw AI analysis data

## Configuration

Edit `config.py` to customize:

- OpenAI API settings
- Screenshot quality and format
- Analysis prompts and focus areas
- Test timeouts and delays
- Report templates

## APTPT/REI/HCE Integration

This testing suite implements your theories:

- **APTPT**: Adaptive, phase-targeted testing with convergence validation
- **REI**: Recursive equivalence testing for consistency and reliability
- **HCE**: Harmonic convergence ensuring optimal user experience

The suite provides:
- **Robust testing** across all user types
- **Convergent validation** of UI/UX quality
- **Adaptive feedback** through AI analysis
- **Human-centered design** validation

## Troubleshooting

### Common Issues

1. **PyAutoGUI not working on macOS**
   - Grant accessibility permissions in System Preferences > Security & Privacy > Privacy > Accessibility
   - Add Terminal/Python to the list of allowed applications

2. **OpenAI API errors**
   - Verify your API key is correct and has sufficient credits
   - Check internet connection
   - Ensure you're using a supported model

3. **Screenshots not taking**
   - Check file permissions in the screenshots directory
   - Ensure the app window is visible and not minimized

4. **Tests timing out**
   - Increase `TEST_TIMEOUT` in `config.py`
   - Check if the app is responding properly

### Debug Mode

Run with verbose output:
```bash
python3 run_all_gui_human_tests.py 2>&1 | tee test_log.txt
```

## Contributing

To add new personas or modify existing ones:

1. Create a new test file following the naming convention
2. Add the persona to the `persona_scripts` list in `run_all_gui_human_tests.py`
3. Update the analysis prompts in `config.py` if needed
4. Test thoroughly before committing

## License

This testing suite is part of the FoS_DeckPro project and follows the same licensing terms.

---

**This testing suite ensures your FoS_DeckPro application meets the highest standards of human-centered design, robustness, and user experience excellence.** 