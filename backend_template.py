
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
                
        
                if trigger_type == "Relation_With_Child":
                    selected_Relation_With_Child = decrypted_data["data"]["Relation_With_Child"]
                    if selected_Relation_With_Child == "":
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
                                "Relation_With_Child_visible": True,
                                "meta_data": decrypted_data["data"]["meta_data"]
                            }
                        }
        
                elif trigger_type == "Title":
                    selected_Title = decrypted_data["data"]["Title"]
                    if selected_Title == "":
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
                                "Title_visible": True,
                                "meta_data": decrypted_data["data"]["meta_data"]
                            }
                        }
        
                elif trigger_type == "Proof_of_Identity":
                    selected_Proof_of_Identity = decrypted_data["data"]["Proof_of_Identity"]
                    if selected_Proof_of_Identity == "":
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
                                "Proof_of_Identity_visible": True,
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
        