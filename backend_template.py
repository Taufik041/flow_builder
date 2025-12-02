
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


            elif "trigger" in decrypted_data["data"]:
                trigger_type = decrypted_data["data"]["trigger"]
                
        
                if trigger_type == "Select_Type_Of_Organization":
                    selected_Select_Type_Of_Organization = decrypted_data["data"]["Select_Type_Of_Organization"]
                    if selected_Select_Type_Of_Organization == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "error": True,
                                "error_message": "Please select correct value"
                            }
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "Select_Type_Of_Organization_visible": True,
                                "meta_data": decrypted_data["data"]["meta_data"]
                            }
                        }
        
                elif trigger_type == "Applicant_Name":
                    selected_Applicant_Name = decrypted_data["data"]["Applicant_Name"]
                    if selected_Applicant_Name == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "error": True,
                                "error_message": "Please select correct value"
                            }
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "Applicant_Name_visible": True,
                                "meta_data": decrypted_data["data"]["meta_data"]
                            }
                        }
        
                elif trigger_type == "Whether_Honble_Governor_Chief_Minister_is_invited_as_Chief_Guest":
                    selected_Whether_Honble_Governor_Chief_Minister_is_invited_as_Chief_Guest = decrypted_data["data"]["Whether_Honble_Governor_Chief_Minister_is_invited_as_Chief_Guest"]
                    if selected_Whether_Honble_Governor_Chief_Minister_is_invited_as_Chief_Guest == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "error": True,
                                "error_message": "Please select correct value"
                            }
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "Whether_Honble_Governor_Chief_Minister_is_invited_as_Chief_Guest_visible": True,
                                "meta_data": decrypted_data["data"]["meta_data"]
                            }
                        }
        
            elif "submit" in decrypted_data['data']:
                submit_type = decrypted_data["data"]["submit"]
        
                if submit_type == "hii":
                    meta_data = decrypted_data["data"]["meta_data"]
                    for key, value in decrypted_data["data"]["form"].items():    
                        if key == "meta_data":
                            continue
                        meta_data[key] = value
                    
                    response = {
                        "screen": decrypted_data["screen"],
                        "data": {
                            "meta_data": meta_data
                        }
                    }

    except Exception as e:
        import traceback; traceback.print_exc();
        response = {
            "screen": decrypted_data["screen"] if "screen" in decrypted_data else "",
            "data": {"error": True, "error_message": "SOME ERROR OCCURED"},
        }
   
    encrypted_response = encrypt_response(response, aes_key, iv)
    return PlainTextResponse(content=encrypted_response, media_type="text/plain")
        