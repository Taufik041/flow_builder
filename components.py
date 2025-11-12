import json, os
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv(override=True)

client = SarvamAI(
    api_subscription_key=os.getenv("SARVAM_API_KEY"),
)

def sarvam_translate(text: str, language: str) -> str:
    response = client.text.translate(
        input=text,
        source_language_code="en-IN",
        target_language_code=language,
        speaker_gender="Male"
    )
    response = dict(response)
    return str(response["translated_text"])

class ComponentBuilder:
    def __init__(self, input_data: dict):
        self.input = input_data
        self.data = {
            "data": {},
            "layout": {
                "type": "SingleColumnLayout",
                "children": []
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
    
    def handle_textsubheading(self, key):
        self.data["layout"]["children"].append({"type": "TextSubheading", "text": self.input[key]["name"]})
    
    def handle_textbody(self, key):
        self.data["layout"]["children"].append({"type": "TextBody", "text": self.input[key]["name"]})
    
    def handle_textcaption(self, key):
        self.data["layout"]["children"].append({"type": "TextCaption", "text": self.input[key]["name"]})
    
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

    def handle_optin(self, key):  
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("'", "").replace("/", "_")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        body = {"type": "OptIn","name": name}
        if reqd_tf:
            body["required"] = "${data.reqd}"
        
        if translate_tf == "en-IN":
            body["label"] = name_original
        else:
            label = sarvam_translate(name_original, translate_tf)
            body["label"] = label
        body["on-select-action"] = {
                "name": "data_exchange",
                "payload": {
                    "trigger": name,
                    name: f"${{form.{name}}}",
                    "meta_data": "${data.meta_data}"
                }
            }
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

    def build_component(self):
        for key in self.input.keys():
            item_type = key.lower()
            if "id" in item_type or "title" in item_type:
                continue
            elif "textinput" in item_type:
                self.handle_textinput(key)
            elif "textheading" in item_type:
                self.handle_textheading(key)
            elif "textsubheading" in item_type:
                self.handle_textsubheading(key)
            elif "textbody" in item_type:
                self.handle_textbody(key)
            elif "textcaption" in item_type:
                self.handle_textcaption(key)
            elif "dropdown" in item_type:
                self.handle_dropdown(key)
            elif "textarea" in item_type:
                self.handle_textarea(key)
            elif "checkboxgroup" in item_type:
                self.handle_checkboxgroup(key)
            elif "radiobuttonsgroup" in item_type:
                self.handle_radiobuttonsgroup(key)
            elif "optin" in item_type:
                self.handle_optin(key)
            else:
                self.handle_default(key)
        return json.dumps(self.data["data"]), json.dumps(self.data["layout"]["children"])
    

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
        }
    }
    builder = ComponentBuilder(input_data)
    data_json, layout_children = builder.build_component()
    # with open("output_flow.json", "w", encoding="utf-8") as f:
    #     f.write(screen_json)
    
    print("***********************************************************************")
    print(data_json)
    print("***********************************************************************")
    print(layout_children)
    print("***********************************************************************")
    