from components import ComponentBuilder
import json

class ScreenBuilder(ComponentBuilder):
    def __init__(self, input_data: dict, screen_name: str):
        super().__init__(input_data)
        id = screen_name.strip().replace(" ", "_").replace("'", "").replace("/","")
        self.data["id"] = id
        self.data["title"] = screen_name
        self.data["terminal"] = True
        self.data["layout"]["children"].append({
                "type": "Footer",
                "label": "Continue",
                "on-click-action": {
                    "name": "data_exchange",
                    "payload": {
                        "footer": id,
                        "form": "${form}",
                        "meta_data": "${data.meta_data}"
                    }
                }
            })
    
    def build_screen(self):
        data_json, layout_children = self.build_component()
        self.data["data"] = json.loads(data_json)
        self.data["layout"]["children"] = json.loads(layout_children)
        swap = self.data["layout"]["children"]
        self.data["layout"]["children"].append(swap.pop(0))
        return json.dumps(self.data, indent=4)
    

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
    
    builder = ScreenBuilder(input_data, "hii")
    data_json = builder.build_screen()
    print(data_json)