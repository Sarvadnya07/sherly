# Sherly UI Design System Specification

**Canonical UI Target**: React 18 + TypeScript + Vite + Tailwind CSS + Tauri 2  
**Transitional Compatibility**: PySide6 Desktop UI  
**Status**: Production-Grade / Active  

---

## 1. Design Principles & Vision

Sherly's user experience is designed as an elite, developer-first desktop AI assistant and workspace copilot.

1. **One Sherly UX**: React + Tauri is the canonical future desktop client. The backend Python core remains authoritative for models, tools, files, tasks, and safety guards.
2. **Obsidian Dark Surface Elevation**: Multi-tiered dark canvas system engineered for long engineering sessions with zero visual fatigue.
3. **Calm, High-Contrast Typography**: Clear hierarchy with WCAG 2.2 AA (and AAA text) compliance.
4. **Resilient Desktop Layout**: Flexible split panes, max-width clamped assistant reading containers (840px), auto-expanding composers, and clean monospace terminals.
5. **Deterministic Status & Approval**: Clear, non-destructive safety confirmation flows for high-risk operations.

---

## 2. Color Palette & Canonical Tokens

### Canvas & Surface Layers
| Token | Hex Value | Purpose |
| :--- | :--- | :--- |
| `--bg-canvas` | `#08080c` | Deepest root application window canvas |
| `--bg-sidebar` | `#0c0c12` | Left vertical navigation rail and project explorer |
| `--bg-surface` | `#101018` | Primary view containers and workspace panels |
| `--bg-card` | `#151520` | Elevated timeline message cards and repository widgets |
| `--bg-card-hover`| `#1a1a28` | Hovered interactive card state |
| `--bg-input` | `#12121c` | Composer and terminal input fields |

### Brand & Accents
| Token | Value | Purpose |
| :--- | :--- | :--- |
| `--brand-primary` | `#7c3aed` (Violet 600) | Primary button fills, active tabs, highlights |
| `--brand-hover` | `#8b5cf6` (Violet 500) | Hovered interactive brand states |
| `--brand-surface` | `rgba(124, 58, 237, 0.12)` | Tinted active tab and badge surfaces |
| `--brand-glow` | `rgba(124, 58, 237, 0.20)` | Subtle shadow elevations |
| `--border-subtle` | `rgba(255, 255, 255, 0.06)` | Structural dividers and cards |
| `--border-medium` | `rgba(255, 255, 255, 0.12)` | Hover borders and dialog edges |
| `--border-focus` | `#9065fc` | Accessible focus-visible outline |

### Semantic Status
| Token | Hex Value | Semantic Role |
| :--- | :--- | :--- |
| `--status-success` | `#10b981` (Emerald 500) | Active models in memory, successful actions, git status |
| `--status-warning` | `#f59e0b` (Amber 500) | Medium-risk operation alerts, offline warnings |
| `--status-danger` | `#f43f5e` (Rose 500) | Destructive action confirmation, error notifications |
| `--status-info` | `#38bdf8` (Sky 400) | Information badges, language syntax marks |

---

## 3. Typography Hierarchy

### Font Families
- **UI & Controls**: `Inter, 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif`
- **Code & Monospace**: `'JetBrains Mono', 'Cascadia Code', Consolas, 'Courier New', monospace`

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

## 4. Spacing Scale (4px Base Grid)

```
Scale: 4px | 8px | 12px | 16px | 20px | 24px | 32px
```
- `gap-1` / `p-1`: 4px — tight button internals and icon gaps
- `gap-2` / `p-2`: 8px — list item spacing and composer padding
- `gap-3` / `p-3`: 12px — sidebar and card layout spacing
- `gap-4` / `p-4`: 16px — standard container and view padding
- `gap-6` / `p-6`: 24px — assistant timeline stream spacing

---

## 5. View Architecture & Information Hierarchy

```
┌────────────────────────────────────────────────────────────────────────┐
│ HeaderBar (44px) [Logo Mark] [Breadcrumbs]    [Model Status Pill] [⚙] [— □ ✕]│
├───────────────┬────────────────────────────────────────────────────────┤
│ Sidebar (240px)│ Main Content Area                                      │
│               │                                                        │
│ [Workspace]   │ 1. AssistantView: Timeline Stream + Docked Composer   │
│ • Assistant   │ 2. WorkspaceView: File Tabs + Code Canvas + Terminal   │
│ • Workspace   │ 3. ModelsView:    Local LLMs + Remote APIs + Inspector │
│               │ 4. VoiceOverlay:  Mic Capsule + Equalizer + Stream     │
│ [Runtime]     │                                                        │
│ • Models      │                                                        │
│ • Voice HUD   │                                                        │
│               │                                                        │
│ [Files Tree]  │                                                        │
│ [▶ Run main]  │                                                        │
└───────────────┴────────────────────────────────────────────────────────┘
```

### Primary Views:
1. **Assistant View (`AssistantView.tsx`)**:
   - Max-width 840px reading container.
   - User cards (with `U` avatar) and Assistant cards (with `S` avatar and `Copilot` badge).
   - Markdown code blocks rendered via `<CodeBlock />` with language headers and one-click copy confirmation.
   - Docked composer with auto-expanding textarea (44px to 140px), file attachment pill, voice trigger, and submit action.
2. **Developer Workspace View (`WorkspaceView.tsx`)**:
   - Tab bar with open files and dirty indicators.
   - Code canvas with line numbers gutter.
   - Diff mode with green added lines, red removed lines, and Accept (`Ctrl+Enter`) / Reject (`Esc`) controls.
   - Integrated terminal runner (`➔ $`) with output streaming and clear action.
   - Git status bar footer.
3. **Model Management View (`ModelsView.tsx`)**:
   - Live Ollama models scan with active status pulse (`● Active in Memory`).
   - Remote Cloud Provider cards (OpenAI, Google Gemini, Groq) with connection status badges and API key modal.
   - Model Inspector panel with hardware memory allocation meters and capability chips.
4. **Voice HUD (`VoiceOverlayView.tsx`)**:
   - Minimalist vector microphone capsule with concentric pulse rings.
   - Live speech-to-text transcription with animated typing indicator.
   - Live audio equalizer bars and hardware device selector dropdown.

---

## 6. Reusable Component System

| Component | Location | Features |
| :--- | :--- | :--- |
| `Button` | `frontend/src/components/ui/Button.tsx` | Primary, secondary, ghost, danger, outline variants; loading spinner; accessible focus. |
| `IconButton` | `frontend/src/components/ui/Button.tsx` | Compact icon actions with required `aria-label` and tooltips. |
| `Badge` | `frontend/src/components/ui/Badge.tsx` | Status tags with optional live pulse dots. |
| `Card` | `frontend/src/components/ui/Card.tsx` | Elevated dark obsidian card containers. |
| `CodeBlock` | `frontend/src/components/ui/CodeBlock.tsx` | Monospace code viewer with language badge, copy action, and horizontal scrolling. |
| `ApprovalDialog` | `frontend/src/components/ui/ApprovalDialog.tsx` | Safety confirmation modal for critical operations (Action, Target, Reason, Risk Level, Reversibility). |

---

## 7. Keyboard Shortcuts & Accessibility

- **Voice Trigger**: `Ctrl + Shift + L`
- **Global Palette / Quick Action**: `Ctrl + Shift + P`
- **Send Assistant Message**: `Enter` (or `Ctrl + Enter` / `Cmd + Enter`)
- **Newline in Composer**: `Shift + Enter`
- **Accept Diff / Confirm**: `Ctrl + Enter`
- **Reject Diff / Close Modal**: `Esc`
- **Focus Rings**: 2px solid `#9065fc` outline with 2px offset on all interactive elements.
