# Claude Design brief — WhatsApp Flow Generator UI

Build the visual UI for an internal developer tool: a chat-based "WhatsApp Flow
Generator". This is a DESIGN task — build the interface and all its visual states with
realistic mock/placeholder data. Do NOT wire it to any API; another step handles that.
Focus entirely on layout, the aesthetic, and rendering every UI state cleanly.

## AESTHETIC — make it feel like Claude.ai (this is the most important instruction)
- Warm, calm, editorial. Warm off-white / cream background (~#F9F8F6), NOT stark white,
  NOT gray, NOT dark.
- Accent: muted terracotta / warm clay (~#C96442). Use it ONLY on primary actions (Send,
  Publish) and active/selected states. Everything else is warm neutral.
- Text is dark warm brown (~#3D3A34), never pure black. Secondary text a muted warm gray.
- Hairline 0.5px borders in low-opacity warm gray. NO heavy boxes, NO drop shadows beyond
  the faintest, NO gradients. Generous whitespace and padding. Restrained type scale.
- Clean neutral sans (Inter). Sentence case everywhere — never Title Case, never ALL CAPS.
- Vibe: a quiet, professional, focused tool. NOT a tech-startup dashboard. Avoid card clutter
  and busy chrome. When in doubt, remove an element and add space.

## LAYOUT — three columns, resizable feel (draggable dividers)
[ Sidebar (collapsible) | Chat (center) | Right output panel ]
- Thin draggable dividers between columns. The sidebar can collapse to a slim rail via a
  chevron toggle.

### LEFT — sessions sidebar
- "New flow" button at top.
- A list of flows (sessions). Each row: a title + a small muted status badge (draft /
  published). Show a few mock rows. The selected row is highlighted with the terracotta accent.
- On hover, a row reveals a small pencil (rename) and trash (delete) icon.
- Logout at the very bottom.
- Design the COLLAPSED state too: a slim rail with just icons.

### CENTER — chat
- Conversation: user messages as soft right-aligned bubbles; assistant content left-aligned.
- Design these assistant STATES (this is the core of the tool — show each as a distinct
  visual treatment):
  1. STREAMING: code/text appearing, with a status pill that reads e.g. "Generating flow…"
  2. VALIDATING: a status pill "Validating against Meta…" with a subtle pulse.
  3. REPAIR — collapsed prior attempt: a collapsed row "Attempt 1 — 2 errors fixed ▸"
     (expandable), shown ABOVE the current expanded attempt.
  4. VALIDATION ERRORS: a small inline panel listing 2 example errors (a short message +
     a faint monospace path), tucked under the relevant attempt.
  5. BACKEND PHASE: a status pill "Writing backend…" after the JSON settles.
  6. DONE: a clean "✓ Flow validated" line.
- GENERATED FILE CHIPS in the chat thread: when a generation finishes, show 2 small
  downloadable file chips inline (like Claude dropping a file) — e.g. "login_flow.json" and
  "login_handler.py", each with a small file icon. These belong in the message history.
- INPUT ROW at the bottom:
  - A textarea with placeholder "Describe your flow, or paste an image…"
  - A paperclip (attach) icon.
  - ATTACHMENT CHIPS above the textarea: design two variants — an IMAGE chip showing a small
    thumbnail + filename + ✕, and a PDF chip showing a doc icon + filename + ✕.
  - A small model dropdown inline (showing e.g. "GPT-4o").
  - A Send button (terracotta, arrow-up icon).
  - Design the disabled/streaming state of the Send button too.

### RIGHT — output panel (single column with a mode toggle)
- Top strip: a [Code] ⇄ [Preview] segmented toggle on the LEFT; copy + download icon
  buttons on the RIGHT of the same strip.
- CODE mode: a small [JSON] / [Backend] sub-switch, and below it a code block with syntax
  highlighting (show realistic mock Flow JSON). Read-only.
- PREVIEW mode: a LARGE phone mockup filling the panel — a clean device frame (rounded bezel,
  notch, phone aspect ratio) containing a mock WhatsApp Flow screen (a "Login" screen with a
  couple of input fields and a green "Continue" button at the bottom, like the real WhatsApp
  Flow preview). Design a FALLBACK state too: the same device frame with a centered
  "Open live preview ↗" button (used when the live preview can't embed).
- BOTTOM of the panel (in Preview mode): a "Deploy" section — an editable text input
  prefilled with a mock endpoint URL (e.g. ".../api/v1/flow/login/login"), a "Save endpoint"
  button, and a "Publish" button (terracotta).
- Design the PUBLISH CONFIRM dialog: a small modal "Publish this flow? — Are you sure?" with
  Cancel / Publish buttons.

## STATES TO DELIVER (don't just design the happy path)
Please show these explicitly so the build has them all:
- Empty state: no flow selected yet (a calm centered prompt to start).
- Streaming + validating + repairing (the pills and collapsed-attempt treatments above).
- Validation-errors inline panel.
- Generated file chips in chat.
- Image attachment chip and PDF attachment chip.
- Preview: phone with mock screen, AND the "Open live preview" fallback.
- Publish confirm modal.
- Collapsed sidebar rail.

## AUTH SCREENS
- /login and /register: minimal, centered, warm. Email + password fields, a primary
  (terracotta) submit button, a link to switch between login/register, and space for an
  inline error message. Same calm aesthetic.

## OUT OF SCOPE (do NOT do these)
- No API calls, no data fetching, no auth logic, no real streaming — mock/placeholder only.
- No code editor in the right panel — it's read-only display for now.
- Don't redesign the architecture — keep the three-panel structure above; only own the visuals.

Deliver the components looking polished and consistent across all the states above, in the
Claude aesthetic. The goal is a shell another step can wire to a live backend without
restructuring anything.
