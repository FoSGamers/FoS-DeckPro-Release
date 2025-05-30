# ManaBox Enhancer UI Style Guide (v1.5.1)

## Overview

ManaBox Enhancer v1.5.1 uses a modern, modular, and consistent UI/UX throughout the application. All components are designed for clarity, accessibility, and ease of use.

## UI/UX Principles
- **Consistency:** All dialogs, overlays, and main windows use a unified style and layout.
- **Accessibility:** Font sizes, colors, and controls are chosen for readability and accessibility.
- **Responsiveness:** All main windows and dialogs are resizable and adapt to different screen sizes.
- **Feedback:** Progress bars, status labels, and confirmation dialogs provide clear feedback for all actions.
- **Error Handling:** All errors are shown with user-friendly messages and safe fallbacks.
- **Separation of Concerns:** Each UI component (main window, dialogs, overlays) is implemented as a separate, reusable module.

## Main Components
- **Main Window:** Central hub for inventory, break builder, and tools.
- **Break/Autobox Builder:** Tabbed interface for filtering, curation, rule-based selection, and preview/export.
- **Dialogs:** Modular dialogs for file selection, ambiguity resolution, and summary/confirmation.
- **Overlays:** Filter overlays and image previews are implemented as reusable widgets.

## Best Practices
- Use only public methods/events for UI communication.
- All new UI features must follow the established style and interaction patterns.
- Document any new UI component or pattern in this guide.

## Notes
- For details on workflows and features, see `README.md`.
- For technical architecture, see `architecture.md`.
