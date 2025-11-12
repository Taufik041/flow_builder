import json, os
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv(override=True)

client = SarvamAI(
    api_subscription_key=os.getenv("SARVAM_API_KEY"),
)

def sarvam_translate(text: str, language: str) -> str:
    # response = client.text.translate(
    #     input=text,
    #     source_language_code="en-IN",
    #     target_language_code=language,
    #     speaker_gender="Male"
    # )
    # response = dict(response)
    # return str(response["translated_text"])
    return ""
class ScreenBuilder:
    def __init__(self, input_data: dict):
        self.input = input_data
        self.data = {
            "id": "",
            "title": "",
            "terminal": True,
            "data": {
                "reqd": {
                    "type": "boolean",
                    "__example__": False
                },
                "meta_data": {
                    "type": "object",
                    "__example__": {}
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "Footer",
                        "label": "Continue",
                        "on-click-action": {
                            "name": "data_exchange",
                            "payload": {
                                "footer": self.input.get("id", "temp"),
                                "form": "${form}",
                                "meta_data": "${data.meta_data}"
                            }
                        }
                    }
                ]
            }
        }

    def handle_textinput(self, key):
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("'", "").replace("/", "_")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        body = {"type": "TextInput", "name": name}

        if translate_tf == "en-IN":
            body["label"] = name_original
        else:
            label = sarvam_translate(name_original, translate_tf)
            body["label"] = label
        if reqd_tf:
            body["required"] = "${data.reqd}"

        self.data["data"][name] = {"type": "string", "__example__": ""}
        self.data["layout"]["children"].append(body)
        
    def handle_textheading(self, key):
        self.data["layout"]["children"].append({"type": "TextHeading", "text": self.input[key]["name"]})

    def handle_dropdown(self, key):  
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("'", "").replace("/", "_")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        body = {"type": "Dropdown","name": name}
        
        if reqd_tf:
            body["required"] = "${data.reqd}"
        
        if translate_tf == "en-IN":
            body["label"] = name_original
        else:
            label = sarvam_translate(name_original, translate_tf)
            body["label"] = label

        body["init-value"] = f"${{data.{name}_init}}"
        body["data-source"] = f"${{data.{name}}}" 
        body["on-select-action"] = {
                "name": "data_exchange",
                "payload": {
                    "trigger": name,
                    name: f"${{form.{name}}}",
                    "meta_data": "${data.meta_data}"
                }
            }    
        self.data["data"][name] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "string"}, "title": {"type": "string"}}
            },
            "__example__": []
        }                
        self.data["data"][f"{name}_init"] = {"type": "string", "__example__": ""}
        self.data["layout"]["children"].append(body)

    def handle_textarea(self, key):
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("/", "_").replace("'", "")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        body = {"type": "TextArea", "name": name}

        if reqd_tf:
            body["required"] = "${data.reqd}"
        if translate_tf == "en-IN":
            body["label"] = name_original
        else:
            label = sarvam_translate(name_original, translate_tf)
            body["label"] = label
        
        self.data["data"][name] = {"type": "string", "__example__": ""}
        self.data["layout"]["children"].append(body)
        # if reqd_tf:
        #     self.data["layout"]["children"].append(
        #         {"type": "TextArea", "label": self.input[key]["name"], "name": name, "required": "${data.reqd}"}
        #     )
        # else:
        #     self.data["layout"]["children"].append(
        #         {"type": "TextArea", "label": self.input[key]["name"], "name": name}
        #     )

    def handle_checkboxgroup(self, key):
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("/", "_").replace("'", "")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        body = {"type": "CheckboxGroup", "name": name, "data-source": f"${{data.{name}}}"}
        
        if reqd_tf:
            body["required"] = "${data.reqd}"
        if translate_tf == "en-IN":
            body["label"] = name_original
        else:
            label = sarvam_translate(name_original, translate_tf)
            body["label"] = label
        
        self.data["data"][name] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "string"}, "title": {"type": "string"}}
            },
            "__example__": [{"id": value,"title": value} for value in self.input[key]["options"]]
        }
        self.data["layout"]["children"].append(body)
            
    def handle_radiobuttonsgroup(self, key):
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("/", "_").replace("'", "")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        body = {"type": "RadioButtonsGroup", "name": name, "data-source": f"${{data.{name}}}"}
        
        if reqd_tf:
            body["required"] = "${data.reqd}"
        if translate_tf == "en-IN":
            body["label"] = name_original
        else:
            label = sarvam_translate(name_original, translate_tf)
            body["label"] = label

        self.data["data"][name] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "string"}, "title": {"type": "string"}}
            },
            "__example__": [{"id": value,"title": value} for value in self.input[key]["options"]]
        }
        self.data["layout"]["children"].append(body)
        
    def handle_default(self, key):
        self.data["layout"]["children"].append({"type": "TextHeading", "text": self.input[key]["name"]})

    def build_flow(self):
        self.data["id"] = self.input.get("id", "temp")
        self.data["title"] = self.input.get("title", "temp")

        for key in self.input.keys():
            item_type = key.lower()
            if "id" in item_type or "title" in item_type:
                continue
            elif "textinput" in item_type:
                self.handle_textinput(key)
            elif "textheading" in item_type:
                self.handle_textheading(key)
            elif "dropdown" in item_type:
                self.handle_dropdown(key)
            elif "textarea" in item_type:
                self.handle_textarea(key)
            elif "checkboxgroup" in item_type:
                self.handle_checkboxgroup(key)
            elif "radiobuttonsgroup" in item_type:
                self.handle_radiobuttonsgroup(key)
            else:
                self.handle_default(key)

        # move Footer to end
        swap_data = self.data["layout"]["children"]
        swap_data.append(swap_data.pop(0))
        self.data["layout"]["children"] = swap_data

        return json.dumps(self.data, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    input_data = {
        "dropdown1": {
            "name": "Select Type Of Organization",
            "required": True,
            "translate": "en-IN"
        },
        "textinput1": {
            "name": "Applicant Name",
            "required": True,
            "translate": "en-IN"
        },
        "textinput2": {
            "name": "Mobile Number",
            "required": True,
            "translate": "en-IN"
        },
        "textinput3": {
            "name": "E-Mail",
            "required": True,
            "translate": "en-IN"
        },
        "dropdown2": {
            "name": "Whether Hon'ble Governor/Chief Minister is invited as Chief Guest",
            "required": True,
            "translate": "en-IN"
        },
        "radiobuttonsgroup1":{
            "name":"R1",
            "required": False,
            "translate":"en-IN",
            "options": ["Yes", "No"]
        },
        
        "checkboxgroup1":{
            "name":"R2",
            "translate":"en-IN",
            "required": False,
            "options": ["Yes", "No"]
        },
        
    }
    builder = ScreenBuilder(input_data)
    screen_json = builder.build_flow()
    with open("output_flow.json", "w", encoding="utf-8") as f:
        f.write(screen_json)
    print("***********************************************************************")
    print(screen_json)
    print("***********************************************************************")