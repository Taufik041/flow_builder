import json, os
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv(override=True)

client = SarvamAI(
    api_subscription_key=os.getenv("SARVAM_API_KEY") or "sk_k0gng5wc_dQcGjY941YtAdlBI8CeHQX0Q",
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
        self.trigger_type = """

            elif "trigger" in decrypted_data["data"]:
                trigger_type = decrypted_data["data"]["trigger"]
                
        """
        self.submit_type = """

            elif "submit" in decrypted_data['data']:
                submit_type = decrypted_data["data"]["submit"]
        """
        self.backend_code = ""

    
    def handle_trigger(self, name, count_trigger):
        if count_trigger == 0:
            self.trigger_type += f"""
                if trigger_type == "{name}":"""
        else:
            self.trigger_type += f"""
                elif trigger_type == "{name}":"""

        self.trigger_type += f"""
                    selected_{name} = decrypted_data["data"]["{name}"]
                    if selected_{name} == "":
                        response = {{
                            "screen": decrypted_data["screen"],
                            "data": {{
                                "error": True,
                                "error_message": "Please select correct value"
                            }}
                        }}
                    else:
                        response = {{
                            "screen": decrypted_data["screen"],
                            "data": {{
                                "{name}_visible": True,
                                "meta_data": decrypted_data["data"]["meta_data"]
                            }}
                        }}
        """
    
    def handle_textinput(self, key):
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("'", "").replace("/", "_").replace("(", "").replace(")", "")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        body = {"type": "TextInput", "name": name, "visible": f"${{data.{name}_visible}}"}

        if translate_tf == "en-IN":
            body["label"] = name_original
        else:
            label = sarvam_translate(name_original, translate_tf)
            body["label"] = label
        if reqd_tf:
            body["required"] = "${data.reqd}"
        
        body["init-value"] = f"${{data.{name}_init}}"
        self.data["data"][f"{name}_init"] = {"type": "string", "__example__": ""}
        self.data["data"][f"{name}_visible"] = {"type": "boolean", "__example__": True}
        self.data["data"][name] = {"type": "string", "__example__": ""}
        self.data["layout"]["children"].append(body)
        
    def handle_textheading(self, key):
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("'", "").replace("/", "_").replace("(", "").replace(")", "")
        self.data["data"][f"{name}_visible"] = {"type": "boolean", "__example__": True}
        self.data["layout"]["children"].append({"type": "TextHeading", "text": name_original, "visible": f"${{data.{name}_visible}}"})

    def handle_textsubheading(self, key):
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("'", "").replace("/", "_").replace("(", "").replace(")", "")
        self.data["data"][f"{name}_visible"] = {"type": "boolean", "__example__": True}
        self.data["layout"]["children"].append({"type": "TextSubheading", "text": name_original, "visible": f"${{data.{name}_visible}}"})
    
    def handle_textbody(self, key):
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("'", "").replace("/", "_").replace("(", "").replace(")", "")
        self.data["data"][f"{name}_visible"] = {"type": "boolean", "__example__": True}
        self.data["layout"]["children"].append({"type": "TextBody", "text": name_original, "visible": f"${{data.{name}_visible}}"})
    
    def handle_textcaption(self, key):
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("'", "").replace("/", "_").replace("(", "").replace(")", "")
        self.data["data"][f"{name}_visible"] = {"type": "boolean", "__example__": True}
        self.data["layout"]["children"].append({"type": "TextCaption", "text": name_original, "visible": f"${{data.{name}_visible}}"})
    
    def handle_dropdown(self, key, count_trigger=0):  
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("'", "").replace("/", "_").replace("(", "").replace(")", "")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        body = {"type": "Dropdown","name": name, "visible": f"${{data.{name}_visible}}"}
        
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
        self.data["data"][f"{name}_visible"] = {"type": "boolean", "__example__": True}
        self.data["data"][f"{name}_init"] = {"type": "string", "__example__": ""}
        self.data["layout"]["children"].append(body)
        self.handle_trigger(name, count_trigger)
        
    def handle_calendarpicker(self, key):
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("'", "").replace("/", "_").replace("(", "").replace(")", "")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        body = {"type": "CalendarPicker","name": name,"helper-text": "Select a date","mode": "single", "visible": f"${{data.{name}_visible}}"}
        
        if reqd_tf:
            body["required"] = "${data.reqd}"
        
        if translate_tf == "en-IN":
            body["label"] = name_original
        else:
            label = sarvam_translate(name_original, translate_tf)
            body["label"] = label

        body["init-value"] = f"${{data.{name}_init}}"
        body["on-select-action"] = {
                "name": "data_exchange",
                "payload": {
                    "trigger": name,
                    name: f"${{form.{name}}}",
                    "meta_data": "${data.meta_data}"
                }
            }
                
        self.data["data"][f"{name}_visible"] = {"type": "boolean", "__example__": True}
        self.data["data"][f"{name}_init"] = {"type": "string", "__example__": ""}
        self.data["layout"]["children"].append(body)

    def handle_datepicker(self, key):  
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("'", "").replace("/", "_").replace("(", "").replace(")", "")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        body = {"type": "DatePicker","name": name, "visible": f"${{data.{name}_visible}}"}
        
        if reqd_tf:
            body["required"] = "${data.reqd}"
        
        if translate_tf == "en-IN":
            body["label"] = name_original
        else:
            label = sarvam_translate(name_original, translate_tf)
            body["label"] = label

        body["init-value"] = f"${{data.{name}_init}}"
        body["on-select-action"] = {
                "name": "data_exchange",
                "payload": {
                    "trigger": name,
                    name: f"${{form.{name}}}",
                    "meta_data": "${data.meta_data}"
                }
            }
                
        self.data["data"][f"{name}_visible"] = {"type": "boolean", "__example__": True}
        self.data["data"][f"{name}_init"] = {"type": "string", "__example__": ""}
        self.data["layout"]["children"].append(body)

    def handle_photopicker(self, key):  
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("'", "").replace("/", "_").replace("(", "").replace(")", "")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        max_file_size = self.input[key].get("max_file_size_kb", 10240)
        body = {
                "type": "PhotoPicker",
                "name": name,
                "description": "Please attach images",
                "photo-source": "camera_gallery",
                "visible": f"${{data.{name}_visible}}",
                "max-file-size-kb": max_file_size
              }
        
        if reqd_tf:
            body["min-uploaded-photos"] = 1
        else:
            body["min-uploaded-photos"] = 0
        
        if translate_tf == "en-IN":
            body["label"] = name_original
        else:
            label = sarvam_translate(name_original, translate_tf)
            body["label"] = label

        body["on-click-action"] = {
                "name": "data_exchange",
                "payload": {
                    "trigger": name,
                    name: f"${{form.{name}}}",
                    "meta_data": "${data.meta_data}"
                }
            }
                
        self.data["data"][f"{name}_visible"] = {"type": "boolean", "__example__": True}
        self.data["layout"]["children"].append(body)

    def handle_optin(self, key):  
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("'", "").replace("/", "_").replace("(", "").replace(")", "")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        body = {"type": "OptIn","name": name, "visible": f"${{data.{name}_visible}}"}
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
        self.data["data"][f"{name}_visible"] = {"type": "boolean", "__example__": True}
        self.data["layout"]["children"].append(body)

    def handle_textarea(self, key):
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("/", "_").replace("'", "").replace("(", "").replace(")", "")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        body = {"type": "TextArea", "name": name, "visible": f"${{data.{name}_visible}}"}

        if reqd_tf:
            body["required"] = "${data.reqd}"
        if translate_tf == "en-IN":
            body["label"] = name_original
        else:
            label = sarvam_translate(name_original, translate_tf)
            body["label"] = label

        body["init-value"] = f"${{data.{name}_init}}"
        self.data["data"][f"{name}_init"] = {"type": "string", "__example__": ""}
        self.data["data"][f"{name}_visible"] = {"type": "boolean", "__example__": True}
        self.data["data"][name] = {"type": "string", "__example__": ""}
        self.data["layout"]["children"].append(body)

    def handle_checkboxgroup(self, key, count_trigger):
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("/", "_").replace("'", "").replace("(", "").replace(")", "")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        body = {"type": "CheckboxGroup", "name": name, "data-source": f"${{data.{name}}}", "visible": f"${{data.{name}_visible}}"}
        
        if reqd_tf:
            body["required"] = "${data.reqd}"
        if translate_tf == "en-IN":
            body["label"] = name_original
        else:
            label = sarvam_translate(name_original, translate_tf)
            body["label"] = label

        body["init-value"] = f"${{data.{name}_init}}"
        self.data["data"][f"{name}_init"] = {"type": "string", "__example__": ""}
        self.data["data"][f"{name}_visible"] = {"type": "boolean", "__example__": True}
        self.data["data"][name] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "string"}, "title": {"type": "string"}}
            },
            "__example__": [{"id": value,"title": value} for value in self.input[key]["options"]]
        }
        self.data["layout"]["children"].append(body)        
        self.handle_trigger(name, count_trigger)
        
        
    def handle_radiobuttonsgroup(self, key):
        name_original = self.input[key]["name"]
        name = name_original.replace(" ", "_").replace("/", "_").replace("'", "").replace("(", "").replace(")", "")
        reqd_tf = self.input[key]["required"]
        translate_tf = self.input[key]["translate"]
        body = {"type": "RadioButtonsGroup", "name": name, "data-source": f"${{data.{name}}}", "visible": f"${{data.{name}_visible}}"}
        
        if reqd_tf:
            body["required"] = "${data.reqd}"
        if translate_tf == "en-IN":
            body["label"] = name_original
        else:
            label = sarvam_translate(name_original, translate_tf)
            body["label"] = label
            
        body["init-value"] = f"${{data.{name}_init}}"
        self.data["data"][f"{name}_init"] = {"type": "string", "__example__": ""}
        self.data["data"][f"{name}_visible"] = {"type": "boolean", "__example__": True}
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
        count_trigger = 0
        count_submit = 0
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
                self.handle_dropdown(key, count_trigger)
                count_trigger += 1
            elif "textarea" in item_type:
                self.handle_textarea(key)
            elif "checkboxgroup" in item_type:
                self.handle_checkboxgroup(key, count_trigger)
                count_trigger +=1
            elif "radiobuttonsgroup" in item_type:
                self.handle_radiobuttonsgroup(key)
            elif "optin" in item_type:
                self.handle_optin(key)
            elif "datepicker" in item_type:
                self.handle_datepicker(key)
            elif "calendarpicker" in item_type:
                self.handle_calendarpicker(key)
            elif "photo_picker" in item_type:
                self.handle_photopicker(key)
            else:
                self.handle_default(key)

        return json.dumps(self.data["data"]), json.dumps(self.data["layout"]["children"]), self.trigger_type
    

if __name__ == "__main__":
    false = False
    input_datas = {
  "image": {
    "dropdown1": {
      "name": "Eyes Type",
      "required": false
    },
    "dropdown2": {
      "name": "Blind",
      "required": false
    },
    "dropdown3": {
      "name": "Eyes Color",
      "required": false
    },
    "dropdown4": {
      "name": "Using Specs",
      "required": false
    },
    "dropdown5": {
      "name": "Specs Type",
      "required": false
    },
    "dropdown6": {
      "name": "Eye Brow Thickness",
      "required": false
    },
    "dropdown7": {
      "name": "Eye Brow Shape",
      "required": false
    },
    "dropdown8": {
      "name": "Blinking",
      "required": false
    },
    "dropdown9": {
      "name": "Squint",
      "required": false
    }
  },
  "add": {},
  "remove": {},
  "type": "components",
  "language": "English",
  "screen_name": "Temp"
}



    input_data = input_datas['image']
    for key, value in input_data.items():
        if "translate" not in input_data[key]:
            input_data[key]["translate"] = "en-IN"
    builder = ComponentBuilder(input_data)
    data_json, layout_children, backend_code = builder.build_component()
    # with open("output_flow.json", "w", encoding="utf-8") as f:
    #     f.write(screen_json)
    
    print("***********************************************************************")
    # print(data_json)
    print("***********************************************************************")
    print(layout_children)
    print("***********************************************************************")
    # print(backend_code)
    print("***********************************************************************")