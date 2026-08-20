# Sherly Canonical UI Design System Specification

**Target Platform**: React 18 + TypeScript + Vite + Tailwind CSS + Tauri 2  
**Version**: 2.0 (Phase 7 Canonicalization)  
**Status**: Production-Grade / Active  

---

## 1. Design Principles & Vision

1. **Quiet, Premium, Developer-First Experience**: Styled with an obsidian canvas and zinc surface elevation for prolonged developer sessions with zero visual fatigue.
2. **Deterministic & Authoritative**: The UI exclusively renders genuine backend metadata. No fabricated metrics (e.g. fake RAM, VRAM, context size, speeds, or fake Git health indicators).
3. **Full Native Selection & Interaction**: The conversation surface maintains complete native clipboard text selection (drag select, double-click word select, Ctrl+A, Ctrl+C, right-click copy, and one-click code copy).
4. **Accessible by Default (WCAG 2.2 AA)**: Explicit focus rings (`2px solid var(--border-focus)` with `2px` offset), high-contrast text tokens, semantic button and icon attributes, and `prefers-reduced-motion` compliance.
5. **Tool & Capability Transparency**: Active tool and capability executions display clear real-time activity chips (e.g. `Executing tool: terminal.execute`, `Reading main.py`) with supported cancellation hooks.

---

## 2. Color Palette & Canonical Semantic Tokens

All semantic design tokens are declared as CSS variables in `frontend/src/index.css` and mapped to Tailwind utilities in `frontend/tailwind.config.cjs`:

### Canvas & Surfaces
| CSS Token | Hex Value | Purpose |
| :--- | :--- | :--- |
| `--bg-canvas` | `#090a0f` | Deepest root application canvas and background |
| `--bg-sidebar` | `#0e0f16` | Left vertical navigation rail and explorer |
| `--bg-surface` | `#12131c` | Workspace and main container backgrounds |
| `--bg-card` | `#171824` | Elevated cards, user prompt bubbles, and model widgets |
| `--bg-card-hover` | `#1d1e2e` | Interactive card and list item hover state |
| `--bg-input` | `#11121b` | Input fields, search bars, and dialog textareas |

### Borders & Focus
| CSS Token | Value | Purpose |
| :--- | :--- | :--- |
| `--border-subtle` | `rgba(255, 255, 255, 0.07)` | Structural dividers, cards, message borders |
| `--border-medium` | `rgba(255, 255, 255, 0.12)` | Active card hover edges, modal dialog borders |
| `--border-focus` | `#8b5cf6` (Violet 500) | 2px accessible focus-visible outline |

### Text & Hierarchy
| CSS Token | Hex Value | Semantic Role |
| :--- | :--- | :--- |
| `--text-primary` | `#f5f5f7` | Primary headings, prompts, active code text |
| `--text-secondary` | `#a1a1aa` | Assistant explanations, descriptions, metadata |
| `--text-muted` | `#71717a` | Section labels, timestamps, icons, line numbers |
| `--text-disabled` | `#52525b` | Disabled buttons and inactive controls |

### Brand & Status
| CSS Token | Hex / RGBA Value | Semantic Role |
| :--- | :--- | :--- |
| `--accent-primary` | `#7c3aed` (Violet 600) | Brand actions, active accents, focus highlights |
| `--accent-primary-hover`| `#8b5cf6` (Violet 500) | Hovered primary buttons and interactive accents |
| `--accent-surface` | `rgba(124, 58, 237, 0.12)` | Brand pill and subtle active surfaces |
| `--status-success` | `#10b981` (Emerald 500) | Running models, successful actions, active status dots |
| `--status-warning` | `#f59e0b` (Amber 500) | Offline warnings, medium-risk alerts |
| `--status-danger` | `#f43f5e` (Rose 500) | Destructive action confirmation, dangerous warnings |
| `--status-info` | `#38bdf8` (Sky 400) | Information badges, tool activity chips |

---

## 3. Typography Hierarchy

### Font Families
- **UI & Interface**: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- **Code & Monospace**: `'JetBrains Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace`

### Typography Scales
| Role | Size | Line Height | Weight | Letter Spacing |
| :--- | :--- | :--- | :--- | :--- |
| **Display** | 20px | 28px | 700 (Bold) | `-0.02em` |
| **Heading** | 15px | 22px | 600 (Semibold) | `-0.01em` |
| **Section Label** | 13px | 18px | 600 (Semibold) | `0.02em` |
| **Body (Default)** | 13px | 20px | 400 (Regular) | `0` |
| **Body Medium** | 12px | 18px | 500 (Medium) | `0` |
| **Caption / Sub** | 11px | 16px | 500 (Medium) | `0` |
| **Code / Mono** | 12px | 18px | 400 / 500 | `0` |
| **Badge / Tag** | 10px | 14px | 600 (Semibold) | `0.05em` |

---

## 4. Spacing Scale (4px Rhythm)

```
4px (1) | 8px (2) | 12px (3) | 16px (4) | 20px (5) | 24px (6) | 32px (8)
```

- `gap-1` / `p-1` (4px): Button internal spacing, icon margins.
- `gap-2` / `p-2` (8px): List items, composer internal controls.
- `gap-3` / `p-3` (12px): Sidebar sections, card internal padding.
- `gap-4` / `p-4` (16px): View containers, header bar margins.
- `gap-6` / `p-6` (24px): Assistant timeline message gaps.

---

## 5. Component Geometry & Standards

| Component | Target Geometry | Radius | Features |
| :--- | :--- | :--- | :--- |
| **HeaderBar** | `44px` height (`h-11`) | `0` | Brand logo, breadcrumb, model status pill, window controls. |
| **Sidebar** | `240px` width (`w-60`) | `0` | Workspace info card, 2px active accent nav, explorer tree, run button. |
| **Button (sm/md/lg)** | `28px` / `32px` / `40px` | `6px` (`rounded-md`) | Accessible focus outline, loading spinner, semantic variants. |
| **IconButton** | `24px` / `28px` / `32px` | `6px` (`rounded-md`) | Mandatory `aria-label` and `title`, subtle hover. |
| **Badge** | `20px` / `24px` height | `4px` (`rounded`) | Semantic status variants, optional pulse dot. |
| **Card** | Flexible | `8px` (`rounded-lg`) | Border-subtle, tokenized card background. |
| **Composer** | `44px` min – `140px` max | `12px` (`rounded-xl`) | Auto-expanding textarea, file pill, send/stop button. |
| **CodeBlock** | Flexible | `8px` (`rounded-lg`) | Syntax header, copy with confirmation, native selection. |
| **ApprovalDialog** | `420px` width | `8px` (`rounded-lg`) | Explicit focus on mount, Enter to Approve, Esc to Reject. |

---

## 6. Keyboard Shortcuts & Accessibility

- **Conversation Search**: `Ctrl + F` (context-aware, opens in-conversation search when active)
- **Send Prompt**: `Enter` (when not holding `Shift`)
- **Newline in Composer**: `Shift + Enter`
- **Stop Generation**: `Esc` (while assistant is generating or thinking)
- **Approve Action**: `Enter` (when approval dialog is focused)
- **Reject Action / Close Modal**: `Esc`
- **Voice HUD**: `Ctrl + Shift + L`
- **Focus Rings**: `2px solid var(--border-focus)` with `2px` offset on all interactive elements.
