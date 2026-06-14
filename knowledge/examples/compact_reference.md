# WhatsApp Flow Compact Reference

## PART 1: Flow JSON Patterns

### Version & Top-Level Structure

```json
{
  "version": "7.3",
  "data_api_version": "3.0",
  "routing_model": {
    "SCREEN_ONE": ["SCREEN_TWO"],
    "SCREEN_TWO": ["SCREEN_THREE"],
    "SCREEN_THREE": []
  },
  "screens": []
}
```

- Default version is **7.3**. Use 7.1 only if explicitly requested.
- In **7.3**: every screen must have `"data": {}` even if empty.
- In **7.1**: `"data": {}` can be omitted entirely.
- The last screen in routing_model has an empty array `[]`.
- Terminal screen (last screen with `complete` action) must have `"terminal": true`.

---

### Screen Structure

```json
{
  "id": "PERSONAL_DETAILS",
  "title": "Personal Details",
  "terminal": false,
  "data": {
    "reqd": { "type": "boolean", "__example__": true },
    "meta_data": { "type": "object", "__example__": {} },
    "caste_data": { "type": "array", "__example__": [{"id":"1","title":"Example"}] },
    "caste_visible": { "type": "boolean", "__example__": false },
    "footer_enabled": { "type": "boolean", "__example__": true }
  },
  "layout": {
    "type": "SingleColumnLayout",
    "children": []
  }
}
```

Rules:
- Screen IDs are SCREAMING_SNAKE_CASE and descriptive (not SCREEN_1, SCREEN_2).
- `"required": "${data.reqd}"` — never use boolean literals for required fields.
- `meta_data` is always declared as `type: object, __example__: {}` in every screen's data block.
- Dynamic arrays (dropdown sources, radio sources) declared as `type: array` in data block.
- Dynamic booleans (visibility, enabled) declared as `type: boolean` in data block.

---

### Footer Payload Convention

Footer always sends `form` and `meta_data`. Never list individual fields.

```json
{
  "type": "Footer",
  "label": "Continue",
  "enabled": "${data.footer_enabled}",
  "on-click-action": {
    "name": "data_exchange",
    "payload": {
      "footer": "SCREEN_ID",
      "form": "${form}",
      "meta_data": "${data.meta_data}"
    }
  }
}
```

Terminal screen footer uses `"name": "complete"` instead of `"data_exchange"`.

---

### Trigger (EmbeddedLink / on-select-action) Payload Convention

Triggers send only the specific field(s) needed plus `meta_data`.

```json
{
  "type": "EmbeddedLink",
  "text": "Search",
  "on-click-action": {
    "name": "data_exchange",
    "payload": {
      "trigger": "caste_search",
      "caste": "${form.caste_input}",
      "meta_data": "${data.meta_data}"
    }
  }
}
```

---

### Backtick Syntax (Mixed Static + Dynamic Strings)

Use backticks when mixing static text with a dynamic value:

```json
"visible": "`${form.present_terms} == '1'`"
```

Pure dynamic references do NOT use backticks:

```json
"data-source": "${data.caste_data}"
"required": "${data.reqd}"
```

---

### PhotoPicker

```json
{
  "type": "PhotoPicker",
  "name": "photo_picker",
  "label": "Applicant Photo",
  "photo-source": "camera_gallery",
  "max-uploaded-photos": 1,
  "min-uploaded-photos": 1,
  "max-file-size-kb": 200
}
```

**Multiple document upload is not currently supported. If asked, inform the user this feature is unavailable.**

Photo upload always pairs with an EmbeddedLink trigger (not footer) for validation:

```json
{
  "type": "EmbeddedLink",
  "text": "Upload",
  "on-click-action": {
    "name": "data_exchange",
    "payload": {
      "trigger": "photo_upload_trigger",
      "photo_picker": "${form.photo_picker}",
      "meta_data": "${data.meta_data}"
    }
  }
}
```

---

### Search-Index Pattern (Data Source > 200 Items)

When a dropdown/radio source exceeds 200 items, use a TextInput + search trigger + conditional RadioButtonsGroup:

```json
{ "type": "TextInput", "name": "caste_input", "label": "Name of your Caste/Tribe", "required": "${data.reqd}" },
{
  "type": "EmbeddedLink",
  "text": "Search your caste/tribe",
  "on-click-action": {
    "name": "data_exchange",
    "payload": { "trigger": "caste_search", "caste": "${form.caste_input}" }
  }
},
{
  "type": "RadioButtonsGroup",
  "name": "selected_caste",
  "label": "Select your caste/tribe",
  "visible": "${data.caste_visible}",
  "data-source": "${data.caste_data}",
  "required": "${data.reqd}",
  "on-select-action": {
    "name": "data_exchange",
    "payload": { "trigger": "caste", "selected_caste": "${form.selected_caste}" }
  }
}
```

Backend returns filtered results and sets `caste_visible: true`.

---

### Conditional Field Groups (type: if)

Use `type: if` to show/hide a group of fields based on a user selection:

```json
{
  "type": "If",
  "condition": "${form.present_permanent} == '2'",
  "then": [
    { "type": "TextSubheading", "text": "Permanent Address" },
    { "type": "Dropdown", "name": "permanent_district", "label": "District", "..." }
  ]
}
```

---

### Dropdown with init-value and on-select-action

```json
{
  "type": "Dropdown",
  "name": "present_district",
  "label": "District",
  "required": "${data.reqd}",
  "init-value": "${data.pre_dist_init}",
  "data-source": "${data.all_pre_district}",
  "on-select-action": {
    "name": "data_exchange",
    "payload": {
      "trigger": "present_district",
      "present_district": "${form.present_district}",
      "meta_data": "${data.meta_data}"
    }
  }
}
```

Backend responds with dependent dropdown data (e.g., subdivisions after district selected).

---

### Dependent Dropdown Chain (District → Subdivision → Village)

Each selection triggers backend to return the next level's data source:

1. `present_district` trigger → backend returns `all_pre_subdivision`
2. `present_subdivision` trigger → backend returns `all_pre_village` (or similar)
3. Village "not in list" fallback → RadioButtonsGroup with single option, reveals TextInput via backtick condition

---

### Component Naming Conventions

| Rule | Example |
|---|---|
| Component `name` | `snake_case` |
| Component `label` | `Title Case` |
| Screen `id` | `SCREAMING_SNAKE_CASE` |
| Trigger string | `snake_case` |
| Footer string | `SCREAMING_SNAKE_CASE` matching screen id |

---

### Full Example Flow (7.1, 3 screens: LOGIN → PERSONAL_DETAILS → ADDRESS)

```json
{
  "version": "7.1",
  "data_api_version": "3.0",
  "routing_model": {
    "LOGIN": ["PERSONAL_DETAILS"],
    "PERSONAL_DETAILS": ["ADDRESS"],
    "ADDRESS": []
  },
  "screens": [
    {
      "id": "LOGIN",
      "title": "Login",
      "data": {
        "reqd": { "type": "boolean", "__example__": true },
        "otp_sent": { "type": "boolean", "__example__": false },
        "meta_data": { "type": "object", "__example__": {} }
      },
      "layout": {
        "type": "SingleColumnLayout",
        "children": [
          { "type": "Image", "src": "BASE64_ENCODED_IMAGE_HERE", "height": 85, "scale-type": "cover" },
          { "type": "TextBody", "font-weight": "bold", "text": "Login for existing users", "visible": true },
          { "type": "TextInput", "name": "user_id", "label": "User ID (Email/Mobile)", "required": "${data.reqd}" },
          {
            "type": "EmbeddedLink",
            "text": "Get OTP",
            "on-click-action": {
              "name": "data_exchange",
              "payload": { "trigger": "get_otp", "username": "${form.user_id}", "meta_data": "${data.meta_data}" }
            }
          },
          { "type": "TextInput", "name": "OTP", "label": "OTP", "input-type": "number", "max-chars": 6, "min-chars": 6, "required": "${data.reqd}" },
          { "type": "OptIn", "name": "consent", "label": "I understand and wish to continue.", "required": true },
          {
            "type": "Footer",
            "label": "Verify OTP",
            "enabled": "${data.otp_sent}",
            "on-click-action": {
              "name": "data_exchange",
              "payload": { "footer": "LOGIN", "form": "${form}", "meta_data": "${data.meta_data}" }
            }
          }
        ]
      }
    },
    {
      "id": "PERSONAL_DETAILS",
      "title": "Personal Details",
      "data": {
        "reqd": { "type": "boolean", "__example__": true },
        "footer_enabled": { "type": "boolean", "__example__": false },
        "caste_visible": { "type": "boolean", "__example__": false },
        "caste_data": { "type": "array", "__example__": [{"id": "1", "title": "Example Caste"}] },
        "Resolution_No": { "type": "array", "__example__": [{"id": "1", "title": "Res 1"}] },
        "meta_data": { "type": "object", "__example__": {} }
      },
      "layout": {
        "type": "SingleColumnLayout",
        "children": [
          {
            "type": "PhotoPicker",
            "name": "photo_picker",
            "label": "Applicant Photo",
            "photo-source": "camera_gallery",
            "max-uploaded-photos": 1,
            "min-uploaded-photos": 1,
            "max-file-size-kb": 200
          },
          {
            "type": "EmbeddedLink",
            "text": "Upload",
            "on-click-action": {
              "name": "data_exchange",
              "payload": { "trigger": "photo_upload_trigger", "photo_picker": "${form.photo_picker}", "meta_data": "${data.meta_data}" }
            }
          },
          { "type": "TextInput", "name": "caste_input", "label": "Name of Your Caste/Tribe", "required": "${data.reqd}" },
          {
            "type": "EmbeddedLink",
            "text": "Search your caste/tribe",
            "on-click-action": {
              "name": "data_exchange",
              "payload": { "trigger": "caste_search", "caste": "${form.caste_input}" }
            }
          },
          {
            "type": "RadioButtonsGroup",
            "name": "selected_caste",
            "label": "Select Your Caste/Tribe",
            "visible": "${data.caste_visible}",
            "data-source": "${data.caste_data}",
            "required": "${data.reqd}",
            "on-select-action": {
              "name": "data_exchange",
              "payload": { "trigger": "caste", "selected_caste": "${form.selected_caste}" }
            }
          },
          {
            "type": "Dropdown",
            "name": "Resolution_No",
            "label": "Resolution No.",
            "required": "${data.reqd}",
            "data-source": "${data.Resolution_No}",
            "on-select-action": {
              "name": "data_exchange",
              "payload": { "trigger": "Resolution_No", "selected_Resolution_No": "${form.Resolution_No}" }
            }
          },
          {
            "type": "Footer",
            "label": "Continue",
            "enabled": "${data.footer_enabled}",
            "on-click-action": {
              "name": "data_exchange",
              "payload": { "footer": "PERSONAL_DETAILS", "form": "${form}", "meta_data": "${data.meta_data}" }
            }
          }
        ]
      }
    },
    {
      "id": "ADDRESS",
      "title": "Address",
      "terminal": true,
      "data": {
        "reqd": { "type": "boolean", "__example__": true },
        "all_pre_district": { "type": "array", "__example__": [{"id": "1", "title": "District 1"}] },
        "all_pre_subdivision": { "type": "array", "__example__": [{"id": "1", "title": "Subdivision 1"}] },
        "pre_dist_init": { "type": "string", "__example__": "" },
        "present_village_enabled": { "type": "boolean", "__example__": true },
        "pre_vill_reqd": { "type": "boolean", "__example__": true },
        "meta_data": { "type": "object", "__example__": {} }
      },
      "layout": {
        "type": "SingleColumnLayout",
        "children": [
          { "type": "TextSubheading", "text": "Present Address" },
          {
            "type": "Dropdown",
            "name": "present_district",
            "label": "District",
            "required": "${data.reqd}",
            "init-value": "${data.pre_dist_init}",
            "data-source": "${data.all_pre_district}",
            "on-select-action": {
              "name": "data_exchange",
              "payload": { "trigger": "present_district", "present_district": "${form.present_district}", "meta_data": "${data.meta_data}" }
            }
          },
          {
            "type": "Dropdown",
            "name": "present_subdivision",
            "label": "Subdivision",
            "required": "${data.reqd}",
            "data-source": "${data.all_pre_subdivision}",
            "on-select-action": {
              "name": "data_exchange",
              "payload": { "trigger": "present_subdivision", "present_subdivision": "${form.present_subdivision}", "meta_data": "${data.meta_data}" }
            }
          },
          {
            "type": "RadioButtonsGroup",
            "name": "present_permanent",
            "label": "Present address same as permanent address?",
            "required": "${data.reqd}",
            "data-source": [{"id": "1", "title": "Yes"}, {"id": "2", "title": "No"}]
          },
          {
            "type": "If",
            "condition": "${form.present_permanent} == '2'",
            "then": [
              { "type": "TextSubheading", "text": "Permanent Address" },
              {
                "type": "Dropdown",
                "name": "permanent_district",
                "label": "District",
                "required": "${data.reqd}",
                "data-source": "${data.all_per_district}",
                "on-select-action": {
                  "name": "data_exchange",
                  "payload": { "trigger": "permanent_district", "permanent_district": "${form.permanent_district}", "meta_data": "${data.meta_data}" }
                }
              }
            ]
          },
          {
            "type": "Footer",
            "label": "Submit",
            "on-click-action": {
              "name": "complete",
              "payload": { "footer": "ADDRESS", "form": "${form}", "meta_data": "${data.meta_data}" }
            }
          }
        ]
      }
    }
  ]
}
```

---

## PART 2: Backend Handler Patterns

### Entry Point Structure

```python
@router.post("/your_flow")
async def your_flow(body: dict = Body(...)):
    decrypted_data, aes_key, iv = decrypt_request(
        body["encrypted_flow_data"],
        body["encrypted_aes_key"],
        body["initial_vector"],
        PHONE_NUMBER_PRIVATE_KEY
    )
    try:
        flow_token = decrypted_data["flow_token"]
        flowid, mobile, user_language = flow_token.split("_")
    except:
        user_language = "en"

    try:
        response = {}

        if decrypted_data["action"] == "ping":
            response = {"data": {"status": "active"}}

        elif decrypted_data["data"] == {}:
            # Initial screen — return first screen with base data
            response = {
                "screen": "LOGIN",
                "data": {
                    "reqd": True,
                    "otp_sent": False,
                    "meta_data": {}
                }
            }

        elif "trigger" in decrypted_data["data"]:
            trigger_type = decrypted_data["data"]["trigger"]
            # ... trigger dispatch below ...

        elif "footer" in decrypted_data["data"]:
            footer_type = decrypted_data["data"]["footer"]
            # ... footer dispatch below ...

    except Exception as e:
        import traceback; traceback.print_exc()
        response = {
            "screen": decrypted_data.get("screen", ""),
            "data": {"error": True, "error_message": "SOME ERROR OCCURRED"}
        }

    encrypted_response = encrypt_response(response, aes_key, iv)
    return PlainTextResponse(content=encrypted_response, media_type="text/plain")
```

---

### Trigger Handlers

**get_otp** — Send OTP and re-render same screen with `otp_sent: True` to enable footer:
```python
elif trigger_type == "get_otp":
    meta_data = decrypted_data["data"].get("meta_data", {})
    meta_data["username"] = decrypted_data["data"].get("username", "")
    # TODO: implement OTP sending logic here
    response = {
        "screen": decrypted_data["screen"],
        "data": {
            "error_message": get_all_messages("OTP_SENT", user_language),
            "meta_data": meta_data,
            "otp_sent": True
        }
    }
```

**photo_upload_trigger** — Validate photo, enable/disable footer:
```python
elif trigger_type == "photo_upload_trigger":
    # TODO: Validate and convert photo to base64
    # Steps a human should implement:
    #   1. Get file from photo_picker[0]
    #   2. Convert to base64 using get_base64_file()
    #   3. Check file size >= 20KB
    #   4. If valid: store base64 in meta_data["photo"], enable footer
    #   5. If invalid: return error, keep footer disabled

    meta_data = decrypted_data["data"].get("meta_data", {})
    photo_valid = False  # TODO: set True after successful validation
    # meta_data["photo"] = base64_photo  # uncomment after validation

    if not photo_valid:
        response = {
            "screen": decrypted_data["screen"],
            "data": {
                "footer_enabled": False,
                "error": True,
                "error_message": get_all_messages("PHOTO_ERROR", user_language)
            }
        }
    else:
        response = {
            "screen": decrypted_data["screen"],
            "data": {
                "footer_enabled": True,
                "error": False,
                "error_message": get_all_messages("UPLOAD_SUCCESS", user_language),
                "meta_data": meta_data
            }
        }
```

**caste_search** — Search-index pattern, filter and return results:
```python
elif trigger_type == "caste_search":
    meta_data = decrypted_data["data"].get("meta_data", {})
    resp_data = {}
    try:
        caste = decrypted_data["data"]["caste"]
        if len(caste) < 3:
            raise Exception("too short")
        caste_list = # TODO: fetch full caste list from API/DB
        filtered = [d for d in caste_list if caste.lower() in d["title"].lower()]
        if not filtered:
            raise Exception("not found")
        resp_data["caste_visible"] = True
        resp_data["caste_data"] = filtered
    except:
        resp_data["error"] = True
        resp_data["error_message"] = get_all_messages("CASTE_ERROR", user_language)
    response = {"screen": decrypted_data["screen"], "data": resp_data}
```

**caste** — Selection triggers dependent data (Resolution No.):
```python
elif trigger_type == "caste":
    selected_caste = decrypted_data["data"].get("selected_caste", "")
    res_no = # TODO: fetch resolution numbers for selected_caste from API
    response = {
        "screen": decrypted_data["screen"],
        "data": {"Resolution_No": res_no}
    }
```

**Dependent dropdown triggers** (district → subdivision → village — same pattern for each):
```python
elif trigger_type == "present_district":
    present_district = decrypted_data["data"]["present_district"]
    # TODO: fetch subdivisions for this district
    response = {
        "screen": decrypted_data["screen"],
        "data": {
            "all_pre_subdivision": [{"id": "1", "title": "Subdivision 1"}],  # TODO: real data
            "pre_dist_init": present_district
        }
    }
```

---

### Footer Handlers

**meta_data accumulation** — Every footer handler does this:
```python
meta_data = decrypted_data["data"].get("meta_data", {})
form = decrypted_data["data"].get("form", {})
meta_data.update(form)
```

**LOGIN footer** — Verify OTP, navigate to next screen:
```python
if footer_type == "LOGIN":
    meta_data = decrypted_data["data"].get("meta_data", {})
    form = decrypted_data["data"].get("form", {})
    meta_data.update(form)
    # TODO: verify OTP here
    # if success:
    response = {
        "screen": "PERSONAL_DETAILS",
        "data": {
            "reqd": True,
            "footer_enabled": False,
            "caste_visible": False,
            "caste_data": [],
            "Resolution_No": [],
            "meta_data": meta_data
        }
    }
    # if fail: return same screen with error_message
```

**PERSONAL_DETAILS footer** — Validate photo in meta_data, navigate to ADDRESS:
```python
elif footer_type == "PERSONAL_DETAILS":
    meta_data = decrypted_data["data"].get("meta_data", {})
    form = decrypted_data["data"].get("form", {})
    meta_data.update(form)

    if "photo" not in meta_data:
        response = {
            "screen": decrypted_data["screen"],
            "data": {"error": True, "error_message": "Upload a photo first"}
        }
    else:
        # TODO: fetch district lists for ADDRESS screen
        response = {
            "screen": "ADDRESS",
            "data": {
                "reqd": True,
                "footer_enabled": True,
                "all_pre_district": [{"id": "1", "title": "District 1"}],  # TODO: real data
                "all_per_district": [{"id": "1", "title": "District 1"}],  # TODO: real data
                "meta_data": meta_data
            }
        }
```

**ADDRESS footer** — Final submission:
```python
elif footer_type == "ADDRESS":
    meta_data = decrypted_data["data"].get("meta_data", {})
    form = decrypted_data["data"].get("form", {})
    meta_data.update(form)
    # TODO: submit full application using meta_data
    response = {
        "screen": "ADDRESS",
        "data": {}
    }
```

---

### Bilingual Support

All user-facing strings go through `get_all_messages()`:

```python
get_all_messages("OTP_SENT", user_language)      # returns string in EN or Odia
get_all_messages("PHOTO_ERROR", user_language)
get_all_messages("UPLOAD_SUCCESS", user_language)
get_all_messages("CASTE_ERROR", user_language)
get_all_messages("LOGIN_SUCCESS", user_language)
get_all_messages("INVALID_OTP", user_language)
```

`user_language` comes from `flow_token.split("_")[2]`, defaults to `"en"`.

---

### Key Rules Summary

1. Footer payload always: `{ "footer": "SCREEN_ID", "form": "${form}", "meta_data": "${data.meta_data}" }`
2. Trigger payload always: `{ "trigger": "trigger_name", <specific_fields>, "meta_data": "${data.meta_data}" }`
3. `meta_data.update(form)` on every footer handler — this accumulates all data across screens
4. `"required": "${data.reqd}"` — never hardcode `true`/`false` for required
5. Backtick syntax for mixed strings: `` "`${form.field} == '1'`" ``
6. Screen response must include ALL data keys the screen declares — missing keys cause errors
7. Multiple document upload is NOT supported — tell the user if asked
8. Leave `# TODO:` comments for API calls, DB queries, business logic — do not hallucinate
