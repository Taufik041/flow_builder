# WhatsApp Flows Knowledge Base
> Paste this at the start of every new session as system context for the Flow Generator Agent.

---

## 1. What This Agent Does

Takes an input (PDF, image, or text description of a form) and outputs:
1. A complete WhatsApp Flow JSON
2. A complete FastAPI backend handler

The agent must never hallucinate. Where context is missing, leave a TODO placeholder. Do not guess business logic, API calls, or message keys.

---

## 2. Version Rules

- Default version: `"7.3"` with `"data_api_version": "3.0"`
- If user specifies `7.1`: use `"7.1"` with `"data_api_version": "3.0"`
- No other versions supported.
- In `7.3`: declare all fields used in the `data` block.
- In `7.1`: the `data` block can be omitted entirely.
- `type: if`, backtick strings, `ChipsSelector`, `ImageCarousel`, empty `data: {}` all require `7.1+`.

---

## 3. Flow JSON Structure

```json
{
    "version": "7.3",
    "data_api_version": "3.0",
    "routing_model": {
        "FIRST_SCREEN_ID": ["SECOND_SCREEN_ID"],
        "SECOND_SCREEN_ID": ["THIRD_SCREEN_ID"],
        "THIRD_SCREEN_ID": []
    },
    "screens": []
}
```

- `routing_model` defines allowed transitions. Every screen must be listed.
- Last screen has an empty array `[]`.
- `screens` is an array of screen objects.

---

## 4. Screen Structure

```json
{
    "id": "DESCRIPTIVE_SCREEN_ID",
    "title": "Screen Title",
    "terminal": false,
    "data": {
        "meta_data": { "type": "object", "__example__": {} },
        "field_name": { "type": "string", "__example__": "" },
        "field_name_init": { "type": "string", "__example__": "" },
        "field_name_visible": { "type": "boolean", "__example__": false }
    },
    "layout": {
        "type": "SingleColumnLayout",
        "children": []
    }
}
```

- `terminal: true` only on the last screen.
- `terminal: false` on all other screens.
- `data` block: declare `meta_data` + every field referenced via `${data.x}`.
- In `7.1`: omit `data` block entirely if preferred.

---

## 5. Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Screen ID | UPPER_SNAKE_CASE, content-based | `PERSONAL_DETAILS_PAGE` |
| Field `name` | snake_case | `applicant_name` |
| Field `label` | Title Case | `"Applicant Name"` |
| Init value key | `{name}_init` | `district_init` |
| Visibility flag | `{name}_visible` | `other_doc_visible` |
| Enable flag | `{name}_enabled` | `footer_enabled` |

---

## 6. meta_data Pattern

- Every screen declares `meta_data` as an empty object in `data`.
- Every footer payload passes `"meta_data": "${data.meta_data}"`.
- Backend merges each screen's form into it:
```python
meta_data = decrypted_data["data"]["meta_data"]
form_data = decrypted_data["data"].get("form", {})
meta_data.update(form_data)
```
- Final `meta_data` on the last screen contains everything for submission.

---

## 7. Footer Payload Pattern

Always use `"form": "${form}"` — never list individual fields.

```json
{
    "type": "Footer",
    "label": "Continue",
    "on-click-action": {
        "name": "data_exchange",
        "payload": {
            "footer": "CURRENT_SCREEN_ID",
            "form": "${form}",
            "meta_data": "${data.meta_data}"
        }
    }
}
```

- `"footer"` value is the **current** screen ID, not the next.
- Backend uses this to know which screen the user is coming from.
- Last screen uses `"submit"` instead of `"footer"`:
```json
"payload": {
    "submit": "FLOW_NAME",
    "form": "${form}",
    "meta_data": "${data.meta_data}"
}
```

---

## 8. Trigger Payload Pattern

For mid-screen interactions (dropdowns, cascades), only send what the trigger needs:

```json
"on-select-action": {
    "name": "data_exchange",
    "payload": {
        "trigger": "field_name",
        "field_name": "${form.field_name}",
        "meta_data": "${data.meta_data}"
    }
}
```

- `"trigger"` value is the field name.
- Only send the triggering field value, not the entire form.

---

## 9. Trigger vs Footer vs Submit Routing

Backend routes on these three keys:

```python
if decrypted_data["data"] == {}:
    # flow opened — return first screen

elif "trigger" in decrypted_data["data"]:
    trigger_type = decrypted_data["data"]["trigger"]
    # mid-screen interaction

elif "footer" in decrypted_data["data"]:
    footer_type = decrypted_data["data"]["footer"]
    # navigate to next screen

elif "submit" in decrypted_data["data"]:
    submit_type = decrypted_data["data"]["submit"]
    # final submission
```

---

## 10. Template Strings (Backtick Syntax)

- Pure dynamic reference → normal quotes: `"${form.name}"`
- Mixed static + dynamic → backticks: `` "`${form.name} is applying for ${form.district}`" ``
- Multiple variables → backticks: `` "`${form.first_name} ${form.last_name}`" ``
- Works in: `label`, `helper-text`, `error-message`, `text`, any string value
- Never use `+` concatenation — only backtick syntax works

---

## 11. Conditional Rendering — `type: if`

```json
{
    "type": "if",
    "condition": "${form.field_name} == 'value'",
    "then": [
        { "type": "TextInput", "name": "conditional_field", "label": "Conditional Field" }
    ],
    "else": []
}
```

- Condition references `${form.x}` — no pre-declaration needed in `7.1+`
- Used for show/hide based on user selection
- `else` can be omitted if empty
- Can be nested

---

## 12. Cascading Dropdowns Pattern

Each dependent dropdown fires a trigger, gets its options from backend, resets all downstream inits to `""`:

**JSON (each dropdown):**
```json
{
    "type": "Dropdown",
    "name": "district",
    "label": "District",
    "init-value": "${data.district_init}",
    "data-source": "${data.district}",
    "on-select-action": {
        "name": "data_exchange",
        "payload": {
            "trigger": "district",
            "district": "${form.district}",
            "meta_data": "${data.meta_data}"
        }
    }
}
```

**Backend (each trigger):**
```python
if trigger_type == "district":
    selected = decrypted_data["data"]["district"]
    if selected == "":
        response = {
            "screen": decrypted_data["screen"],
            "data": { "error": True, "error_message": get_all_messages("SELECT_VALID", user_language) }
        }
    else:
        # TODO: call API to get subdivisions for selected district
        response = {
            "screen": decrypted_data["screen"],
            "data": {
                "subdivision": [],          # populated from API
                "subdivision_init": "",     # reset downstream
                "tehsil": [],
                "tehsil_init": "",
                "meta_data": decrypted_data["data"]["meta_data"]
            }
        }
```

---

## 13. Large Dropdown Workaround (200+ items) — Search Pattern

WhatsApp Flows has a 200-item limit on dropdown/radio data sources.

**Workaround:** TextInput + EmbeddedLink + RadioButtonsGroup. TextInput has NO
trigger mechanism — it cannot talk to the backend. The EmbeddedLink next to it
is the bridge: its on-click-action reads the typed value via ${form.x} and
fires the search trigger. Results return into an initially-hidden
RadioButtonsGroup.

**JSON:**
```json
{
    "type": "TextInput",
    "name": "caste_input",
    "required": "${data.reqd}",
    "label": "Name of your Caste/Tribe"
},
{
    "type": "EmbeddedLink",
    "text": "Search your caste/tribe",
    "on-click-action": {
        "name": "data_exchange",
        "payload": {
            "trigger": "caste_search",
            "caste": "${form.caste_input}"
        }
    }
},
{
    "type": "RadioButtonsGroup",
    "name": "Caste",
    "label": "Select your caste/tribe",
    "visible": "${data.caste_visible}",
    "data-source": "${data.caste_data}",
    "required": "${data.reqd}",
    "on-select-action": {
        "name": "data_exchange",
        "payload": {
            "trigger": "caste",
            "selected_caste": "${form.Caste}"
        }
    }
}
```

**Backend (caste_search trigger):**
```python
elif trigger_type == "caste_search":
    resp_data = {}
    try:
        caste = decrypted_data["data"]["caste"]
        if len(caste) < 3:  # minimum 3 chars, enforced in backend
            resp_data["error"] = True
            resp_data["error_message"] = get_all_messages("CASTE_ERROR_NOT_ENOUGH", user_language)
            raise Exception("length less than 3")
        caste_list = sebcCertAPI.getCaste()  # TODO: replace with actual API
        show_d = [d for d in caste_list if caste.lower() in d["title"].lower()]
        if not show_d:
            resp_data["error"] = True
            resp_data["error_message"] = get_all_messages("CASTE_ERROR", user_language)
            raise Exception("Caste not found")
        resp_data["caste_visible"] = True
        resp_data["caste_data"] = show_d
    except:
        resp_data["error"] = True
        resp_data["error_message"] = get_all_messages("CASTE_ERROR", user_language)
    response = {
        "screen": decrypted_data["screen"],
        "data": resp_data
    }
```

**Key rules:**
- TextInput has no backend trigger — EmbeddedLink is always the bridge
- Minimum search length validated in backend (3 chars), not in JSON
- Substring match, case-insensitive
- Selection component starts hidden via `_visible` flag, shown when results return
- Errors keep user on same screen with a bilingual message

---

## 14. Error Handling Pattern

**User error (bad input):** Stay on same screen.
```python
response = {
    "screen": decrypted_data["screen"],
    "data": {
        "error": True,
        "error_message": get_all_messages("TODO_KEY", user_language)
    }
}
```

**API error:** Stay on same screen, generic message.
```python
response = {
    "screen": decrypted_data["screen"],
    "data": {
        "error": True,
        "error_message": get_all_messages("API_ERROR", user_language)
    }
}
```

**Flow exception (catch-all):**
```python
except Exception as e:
    import traceback; traceback.print_exc()
    response = {
        "screen": decrypted_data["screen"] if "screen" in decrypted_data else "",
        "data": { "error": True, "error_message": "SOME ERROR OCCURED" }
    }
```

---

## 15. Bilingual Support

- Two languages: `en` (English), `od` (Odia)
- All user-facing strings: `get_all_messages("MESSAGE_KEY", user_language)`
- Returns a plain string — no special handling needed
- `user_language` extracted from `flow_token`
- If message key is unknown: `get_all_messages("TODO_KEY", user_language)`

---

## 16. Static / POC Mode

For demos with no backend:
- Use hardcoded `true` for `required` fields — never `"${data.reqd}"`
- No `data_exchange` on footers — use `"name": "navigate"` instead
- No `${data.x}` references that require backend to populate
- `type: if` still works for UI logic

---

## 17. DB Logging

Every transition logged to `FlowLogs`:
```python
# fields: current (screen name), msg, type, error
# type values: INFO | USER_ERROR | API_ERROR | FLOW_ERROR
```

`screen_mapper` maps screen IDs to readable names:
```python
screen_mapper = {
    "PERSONAL_DETAILS_PAGE": "Personal Details",
    "ADDRESS_PAGE": "Address",
    # ...
}
```

---

## 18. Complete Backend Boilerplate

```python
from fastapi import APIRouter, Body
from fastapi.responses import PlainTextResponse
from core.keys import PHONE_NUMBER_PRIVATE_KEY
from utils.fb_utils import decrypt_request, encrypt_response

router = APIRouter()

@router.post("/flow_name")
async def flow_name_handler(body: dict = Body(...)):
    encrypt_flow_data_b64 = body["encrypted_flow_data"]
    encrypt_aes_key_b64 = body["encrypted_aes_key"]
    initial_vector_b64 = body["initial_vector"]
    decrypted_data, aes_key, iv = decrypt_request(
        encrypt_flow_data_b64,
        encrypt_aes_key_b64,
        initial_vector_b64,
        PHONE_NUMBER_PRIVATE_KEY
    )
    try:
        if decrypted_data["action"] == "ping":
            response = {"data": {"status": "active"}}

        else:
            # Extract language from flow_token: "flowid_mobile_language"
            user_language = decrypted_data.get("flow_token", "__en").split("_")[-1]

            if decrypted_data["data"] == {}:
                response = {
                    "screen": "FIRST_SCREEN_ID",
                    "data": {
                        "reqd": True,
                        "meta_data": {},
                        # TODO: populate any init data for first screen
                    }
                }

            elif "trigger" in decrypted_data["data"]:
                trigger_type = decrypted_data["data"]["trigger"]

                if trigger_type == "field_name":
                    selected = decrypted_data["data"]["field_name"]
                    if selected == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "error": True,
                                "error_message": get_all_messages("SELECT_VALID", user_language)
                            }
                        }
                    else:
                        # TODO: call API to get dependent data
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "dependent_field": [],
                                "dependent_field_init": "",
                                "meta_data": decrypted_data["data"]["meta_data"]
                            }
                        }
                # ... one block per trigger

            elif "footer" in decrypted_data["data"]:
                footer_type = decrypted_data["data"]["footer"]

                if footer_type == "CURRENT_SCREEN_ID":
                    meta_data = decrypted_data["data"]["meta_data"]
                    for key, value in decrypted_data["data"].get("form", {}).items():
                        if key == "meta_data":
                            continue
                        meta_data[key] = value
                    response = {
                        "screen": "NEXT_SCREEN_ID",
                        "data": {
                            "reqd": True,
                            "meta_data": meta_data,
                            # TODO: populate any init data for next screen
                        }
                    }
                # ... one block per footer

            elif "submit" in decrypted_data["data"]:
                submit_type = decrypted_data["data"]["submit"]

                if submit_type == "FLOW_NAME":
                    meta_data = decrypted_data["data"]["meta_data"]
                    for key, value in decrypted_data["data"].get("form", {}).items():
                        if key == "meta_data":
                            continue
                        meta_data[key] = value
                    # TODO: submit meta_data to API
                    response = {
                        "screen": decrypted_data["screen"],
                        "data": { "meta_data": meta_data }
                    }

    except Exception as e:
        import traceback; traceback.print_exc()
        response = {
            "screen": decrypted_data["screen"] if "screen" in decrypted_data else "",
            "data": { "error": True, "error_message": "SOME ERROR OCCURED" }
        }

    encrypted_response = encrypt_response(response, aes_key, iv)
    return PlainTextResponse(content=encrypted_response, media_type="text/plain")
```

---

## 19. Agent TODO Rules

| Situation | What agent outputs |
|---|---|
| Unknown API call | `# TODO: call API to get {field} data` |
| Unknown message key | `get_all_messages("TODO_KEY", user_language)` |
| Unknown business logic | `# TODO: add logic here` |
| Unknown screen fields | Screen stub with `# TODO: add components` |
| Unknown init data | `# TODO: populate init data for this screen` |
| Unknown submission endpoint | `# TODO: submit meta_data to API` |

---

## 20. Available Components

| Component | Type string | Notes |
|---|---|---|
| Text heading | `TextHeading` | Static |
| Text subheading | `TextSubheading` | Static |
| Text body | `TextBody` | Static, supports markdown |
| Text caption | `TextCaption` | Static, supports markdown |
| Text input | `TextInput` | Single line |
| Text area | `TextArea` | Multi line |
| Dropdown | `Dropdown` | Needs `data-source`, `init-value`, `on-select-action` |
| Radio buttons | `RadioButtonsGroup` | Needs `data-source` |
| Checkbox group | `CheckboxGroup` | Needs `data-source` |
| Chips selector | `ChipsSelector` | 7.1+ |
| Calendar picker | `CalendarPicker` | 6.1+ |
| Date picker | `DatePicker` | Older, use CalendarPicker if 6.1+ |
| Photo picker | `PhotoPicker` | 4.0+ |
| Document picker | `DocumentPicker` | 4.0+ |
| Image | `Image` | Static image |
| Image carousel | `ImageCarousel` | 7.1+, multiple images |
| Embedded link | `EmbeddedLink` | Can open external URLs |
| Rich text | `RichText` | Markdown support |
| Opt-in | `OptIn` | Checkbox with label |
| Footer | `Footer` | Always last child, one per screen |
| If block | `if` | Conditional rendering, 6.0+ |
| Switch block | `switch` | Multi-condition rendering, 6.0+ |

---

## 21. Adding New Workarounds

When a new pattern or workaround is discovered, add a section here following this format:

```
### WA-XXX: Short Title

**Problem:** What fails and why.
**Workaround:** What to do instead.
**Example:** Minimal code snippet.
**Versions:** Which versions this applies to.
```

Current workarounds:
- **WA-001** (Section 13): Large dropdown >200 items → TextInput + EmbeddedLink trigger + hidden RadioButtonsGroup
- **WA-002** (Section 10): Mixed static+dynamic strings → use backtick syntax

---

## Source Integrity Rule

Every JSON pattern and backend snippet in this knowledge base must come from
working production code or verified Meta documentation. Never reconstruct
patterns from memory or invent plausible-looking syntax. If the real
implementation is unknown, write a TODO and ask — an honest gap is recoverable,
a confident hallucination is not.