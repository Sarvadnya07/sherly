## 2024-05-18 - Missing tooltips on icon-only buttons
**Learning:** PySide6/Qt desktop UIs often neglect screen-reader and hover accessibility for icon-only buttons (like settings, power, close). Similarly, web interfaces can omit native `title`s or `aria-label`s.
**Action:** Always check `QPushButton` for `.setToolTip()` and web `<button>` elements for `title` and `aria-label` when they only contain icons or emojis.
