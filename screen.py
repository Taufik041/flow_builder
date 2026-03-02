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
                        "submit": id,
                        "form": "${form}",
                        "meta_data": "${data.meta_data}"
                    }
                }
            })
        self.submit_type = ""
        self.backend_code = """
from fastapi import APIRouter, Body, Depends
from fastapi.responses import PlainTextResponse
from core.keys import PHONE_NUMBER_PRIVATE_KEY
from utils.fb_utils import decrypt_request, encrypt_response


router = APIRouter()

@router.post("/router")
async def router1(body: dict = Body(...)):
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
        if decrypted_data['action'] == 'ping':
            response = {
                "data": {"status": "active"}
            }
        else:
       
            if decrypted_data['data'] == {}:
                response = {
                    "screen": "LOGIN",
                    "data": {
                        "reqd": True,
                        "meta_data": {}
                    }
                }
"""
    def build_submit_code(self, submit_count: int):
        id = self.data["id"]
        self.submit_type = f"""
            elif "submit" in decrypted_data['data']:
                submit_type = decrypted_data["data"]["submit"]
        """
        if submit_count == 0:
            self.submit_type += f"""
                if submit_type == "{id}":
                    meta_data = decrypted_data["data"]["meta_data"]
                    for key, value in decrypted_data["data"]["form"].items():    
                        if key == "meta_data":
                            continue
                        meta_data[key] = value
                    
                    response = {{
                        "screen": decrypted_data["screen"],
                        "data": {{
                            "meta_data": meta_data
                        }}
                    }}"""
        else:
            self.submit_type += f"""
                elif submit_type == "{id}":
                    meta_data = decrypted_data["data"]["meta_data"]
                    form = decrypted_data["data"]["form"]
                    for key, value in form.items():
                        if key == "meta_data":
                            continue
                        meta_data[key] = value
                    
                    response = {{
                        "screen": decrypted_data["screen"],
                        "data": {{
                            "meta_data": meta_data,
                            "reqd": True
                        }}
                    }}"""
        return self.submit_type
    
    
    def build_backend_code(self, trigger_data, submit_data):    
        self.backend_code += trigger_data
        self.backend_code += submit_data
        self.backend_code += """

    except Exception as e:
        import traceback; traceback.print_exc();
        response = {
            "screen": decrypted_data["screen"] if "screen" in decrypted_data else "",
            "data": {"error": True, "error_message": "SOME ERROR OCCURED"},
        }
   
    encrypted_response = encrypt_response(response, aes_key, iv)
    return PlainTextResponse(content=encrypted_response, media_type="text/plain")
        """
        return self.backend_code
        
        
    def build_screen(self):
        data_json, layout_children, trigger_code = self.build_component()
        self.data["data"] = json.loads(data_json)
        self.data["layout"]["children"] = json.loads(layout_children)
        swap = self.data["layout"]["children"]
        self.data["layout"]["children"].append(swap.pop(0))
        
        submit_code: str = self.build_submit_code(0)
        backend_code: str = self.build_backend_code(trigger_code, submit_code)
        
        with open("backend_template.py", "w", encoding="utf-8") as f:
            f.write(backend_code)
        return json.dumps(self.data, indent=4), backend_code
    

if __name__ == "__main__":
    false = False
    true = True
    input_datas = {
  "image": {
    "textheading1": {
      "name": "Applicant Details",
      "required": false
    },
    "dropdown1": {
      "name": "Relation With Child",
      "required": true
    },
    "dropdown2": {
      "name": "Title",
      "required": false
    },
    "textinput1": {
      "name": "Applicant's First Name",
      "required": true
    },
    "textinput2": {
      "name": "Applicant's middle Name",
      "required": false
    },
    "textinput3": {
      "name": "Applicant's Last Name",
      "required": false
    },
    "dropdown3": {
      "name": "Proof of Identity",
      "required": true
    },
    "textinput4": {
      "name": "Proof of Identity No",
      "required": true
    },
    "textinput5": {
      "name": "Mobile No",
      "required": true
    },
    "radiobuttonsgroup1": {
      "name": "Set WhatsApp No same as your Mobile No",
      "required": false,
      "options": [
        "Yes",
        "No"
      ]
    },
    "textinput6": {
      "name": "WhatsApp Mobile Number",
      "required": false
    },
    "textinput7": {
      "name": "Email ID",
      "required": false
    }
  },
  "add": {},
  "remove": {},
  "type": "components",
  "language": "English",
  "screen_name": "temp"
}
    
    input_data = input_datas['image']
    for key, value in input_data.items():
        if "translate" not in input_data[key]:
            input_data[key]["translate"] = "en-IN"
    # input_data = {
    #         "dropdown1": {
    #             "name": "Select Type Of Organization",
    #             "required": True,
    #             "translate": "en-IN"
    #         },
    #         "checkboxgroup1": {
    #             "name": "Applicant Name",
    #             "required": True,
    #             "translate": "en-IN",
    #             "options": ["Org A", "Org B", "Org C"]
    #         },
    #         "textinput2": {
    #             "name": "Mobile Number",
    #             "required": True,
    #             "translate": "en-IN"
    #         },
    #         "textinput3": {
    #             "name": "E-Mail",
    #             "required": True,
    #             "translate": "en-IN"
    #         },
    #         "dropdown2": {
    #             "name": "Whether Hon'ble Governor/Chief Minister is invited as Chief Guest",
    #             "required": True,
    #             "translate": "en-IN"
    #         }
    #     }
    
    builder = ScreenBuilder(input_data, "hii")
    data_json, j = builder.build_screen()
    print(data_json)
    print("="*50)
    print(j)