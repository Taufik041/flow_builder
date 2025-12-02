from fastapi import APIRouter, Body, Depends
from fastapi.responses import PlainTextResponse
from core.keys import PHONE_NUMBER_PRIVATE_KEY
from utils.fb_utils import decrypt_request, encrypt_response
from services import income_certificateApis
from jsondata.LANDREG.extra_data import income_tehsil

income_router = APIRouter()

@income_router.post("/income")
async def income(body: dict = Body(...)):
    state = [{"id": "21_Odisha", "title": "Odisha"}]
    
    encrypt_flow_data_b64 = body["encrypted_flow_data"]
    encrypt_aes_key_b64 = body["encrypted_aes_key"]
    initial_vector_b64 = body["initial_vector"]
    incCertAPI = income_certificateApis.IncomeCertificateAPI()
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
               
                if trigger_type == "salutation":
                    salutation = decrypted_data["data"]["salutation"]
                    meta_data = decrypted_data["data"].get("meta_data", {})
                    gender = incCertAPI.getGender(salutation)
                    marital_status = incCertAPI.getMaritalStatus(salutation)
                    response = {
                        "screen": "SCREEN_ONE",
                        "data": {
                            "gender": gender,
                            "marital_status": marital_status,
                            "meta_data": meta_data
                        }
                    }
                elif trigger_type=='want_register':
                    response = {
                        "screen": "REGISTRATION",
                        "data": {
                            "registered": False
                        }
                    }
                elif trigger_type=='register':
                    
                    if 'name' not in decrypted_data['data'] or 'email' not in decrypted_data['data']  or 'mobile' not in decrypted_data['data'] :
                        response = {
                            "screen": decrypted_data['screen'],
                            "data": {
                                "registered": False,
                                "error_message": "Please fill all the informations"
                            }
                        }
                    else:
                        name=decrypted_data['data']['name']
                        email=decrypted_data['data']['email']
                        mobile=decrypted_data['data']['mobile']
                        reg_response=incCertAPI.register(name, email, mobile)
                        if reg_response['status_code']==200:
                            response = {
                                "screen": decrypted_data['screen'],
                                "data": {
                                    "registered": True,
                                    "password_url": reg_response['verificationLink']
                                }
                            }
                        else:
                            response = {
                                "screen": decrypted_data['screen'],
                                "data": {
                                    "registered": False,
                                    "error_message": reg_response['remarks']
                                }
                            }
               
                elif trigger_type == "present_district":
                    present_district = decrypted_data["data"]["present_district"]
                    sub_list = incCertAPI.getSubdivision(int(present_district.split("_")[0]))
                    response = {
                        "screen": "SCREEN_TWO",
                        "data": {
                            "all_pre_subdivision": sub_list
                        }
                    }

                elif trigger_type == "present_subdivision":
                    present_subdivision = decrypted_data["data"]["present_subdivision"]
                    teh_list = incCertAPI.getTehsil(int(present_subdivision.split("_")[0]))
                    response = {
                        "screen": "SCREEN_TWO",
                        "data": {
                            "all_pre_tehsil": teh_list
                        }
                    }
                   
                elif trigger_type == "present_tehsil":
                    present_tehsil = decrypted_data["data"]["present_tehsil"]
                    ri = incCertAPI.getRi(int(present_tehsil.split("_")[0]))
                    response = {
                        "screen": "SCREEN_TWO",
                        "data": {
                            "all_pre_ricircle": ri
                        }
                    }

                elif trigger_type == "present_ri_circle":
                    present_ri_circle = decrypted_data["data"]["present_ri_circle"]
                    village = incCertAPI.getVillage(int(present_ri_circle.split("_")[0]))
                    if village == []:
                        response = {
                            "screen": "SCREEN_TWO",
                            "data": {
                                "all_pre_village": []
                            }
                        }
                    else:
                        response = {
                            "screen": "SCREEN_TWO",
                            "data": {
                                "all_pre_village": village
                            }
                        }
                
                elif trigger_type == "present_village":
                    present_village = decrypted_data["data"]["present_village"]
                    response = {
                        "screen": "SCREEN_TWO",
                        "data": {
                            "present_village_init": present_village
                        }
                    }
                
                elif trigger_type == "permanent_village":
                    permanent_village = decrypted_data["data"]["permanent_village"]
                    response = {
                        "screen": "SCREEN_TWO",
                        "data": {
                            "permanent_village_init": permanent_village
                        }
                    }
               
                elif trigger_type == "present_terms":
                    present_terms = decrypted_data["data"].get("present_terms", "")
                    
                    if present_terms == "":
                        response = {
                            "screen": "SCREEN_TWO",
                            "data": {
                                "present_village_enabled": True,
                                "pre_vill_reqd": True,
                            }
                        }
                    else:
                        response = {
                            "screen": "SCREEN_TWO",
                            "data": {
                                "present_village_enabled": False,
                                "pre_vill_reqd": False,
                            }
                        }
                
                elif trigger_type == "permanent_terms":
                    permanent_terms = decrypted_data["data"].get("permanent_terms", "")
                    
                    if permanent_terms == "":
                        response = {
                            "screen": "SCREEN_TWO",
                            "data": {
                                "permanent_village_enabled": True,
                                "per_vill_reqd": True,
                            }
                        }
                    else:
                        response = {
                            "screen": "SCREEN_TWO",
                            "data": {
                                "permanent_village_enabled": False,
                                "per_vill_reqd": False,
                            }
                        }
               
                elif trigger_type == "permanent_state":
                    permanent_state = decrypted_data["data"]["permanent_state"]
                    district = incCertAPI.getDistricts()
                    response = {
                        "screen": "SCREEN_TWO",
                        "data": {
                            "all_per_district": district
                        }
                    }
               
                elif trigger_type == "permanent_district":
                    permanent_district = decrypted_data["data"]["permanent_district"]
                    subdivision = incCertAPI.getSubdivision(int(permanent_district.split("_")[0]))
                    response = {
                        "screen": "SCREEN_TWO",
                        "data": {
                            "all_per_subdivision": subdivision
                        }
                    }
                elif trigger_type == "permanent_subdivision":
                    permanent_subdivision = decrypted_data["data"]["permanent_subdivision"]
                    teh_list = incCertAPI.getTehsil(int(permanent_subdivision.split("_")[0]))
                    response = {
                        "screen": "SCREEN_TWO",
                        "data": {
                            "all_per_tehsil": teh_list
                        }
                    }
                
                elif trigger_type == "permanent_tehsil":
                    permanent_tehsil = decrypted_data["data"]["permanent_tehsil"]
                    ri = incCertAPI.getRi(int(permanent_tehsil.split("_")[0]))
                    response = {
                        "screen": "SCREEN_TWO",
                        "data": {
                            "all_per_ricircle": ri
                        }
                    }
               
                elif trigger_type == "permanent_ri_circle":
                    permanent_ri_circle = decrypted_data["data"]["permanent_ri_circle"]
                    village = incCertAPI.getVillage(int(permanent_ri_circle.split("_")[0]))
                    if village == []:
                        response = {
                            "screen": "SCREEN_TWO",
                            "data": {
                                "all_per_village": []
                            }
                        }
                    else:
                        response = {
                            "screen": "SCREEN_TWO",
                            "data": {
                                "all_per_village": village
                            }
                    }
                
                elif trigger_type == "upload":
                    document_name_other_visible = False
                    DOC_MAP = {
                        "Document": "copy_of_ROR",
                        "copy_of_ROR": "Salary_Certificate_if_any",
                        "Salary_Certificate_if_any": "IT_returns_if_any",
                        "IT_returns_if_any": "Documents_in_support_other_income",
                        "Documents_in_support_other_income": "Other"
                    }
                    meta_data = decrypted_data["data"]["meta_data"]
                    for key, value in decrypted_data["data"].items(): 
                        if key == "meta_data":
                            continue
                        meta_data[key] = value
                    
                    upload_type = decrypted_data["data"].get("upload_type", "")
                    Document_to_be_attached = decrypted_data["data"].get("Document_to_be_attached", "")
                    Document = decrypted_data["data"].get("Document", "")
                    copy_of_ROR = decrypted_data["data"].get("copy_of_ROR", "")
                    Salary_Certificate_if_any = decrypted_data["data"].get("Salary_Certificate_if_any", "")
                    IT_returns_if_any = decrypted_data["data"].get("IT_returns_if_any", "")
                    Documents_in_support_other_income = decrypted_data["data"].get("Documents_in_support_other_income", "")
                    Other = decrypted_data["data"].get("Other", "")
                    
                    if upload_type == "Document":
                        if Document_to_be_attached:
                            meta_data[Document_to_be_attached] = Document
                    else:
                        # meta_data[upload_type] = upload_type
                        if upload_type == "copy_of_ROR":
                            meta_data[upload_type] = copy_of_ROR
                        elif upload_type == "Salary_Certificate_if_any":
                            meta_data[upload_type] = Salary_Certificate_if_any
                        elif upload_type == "IT_returns_if_any":
                            meta_data[upload_type] = IT_returns_if_any
                        elif upload_type == "Documents_in_support_other_income":
                            meta_data[upload_type] = Documents_in_support_other_income
                            document_name_other_visible = True
                        elif upload_type == "Other":
                            document_name_other = decrypted_data["data"].get("document_name_other", "")
                            meta_data[document_name_other] = Other
                   
                    if upload_type in ["Document", "copy_of_ROR", "Salary_Certificate_if_any", "IT_returns_if_any", "Documents_in_support_other_income"]:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "reqd": True,
                                "meta_data": meta_data,
                                "document_name_other_visible": document_name_other_visible,
                                "upload_type": DOC_MAP[upload_type],
                                "button_activate": True,
                                "document_to_be_attached_visible": False,
                                "skip_visible": True
                            }
                        }
                    elif upload_type == "Other":
                        if Other and document_name_other:
                            response = {
                                "screen": decrypted_data["screen"],
                                "data": {
                                    "reqd": True,
                                    "meta_data": meta_data,
                                    "final_visible": True,
                                    "document_name_other_visible": False,
                                    "upload_show": False,
                                    "button_activate": True,
                                    "document_to_be_attached_visible": False,
                                }
                            }
                        else:
                            response = {
                                "screen": decrypted_data["screen"],
                                "data": {
                                    "error": True,
                                    "error_message": "Please enter document name and upload the document",
                                }
                            }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "error": True,
                                "error_message": "Please upload the document",
                            }
                    }
                
            elif "footer" in decrypted_data['data']:
                footer_type = decrypted_data["data"]["footer"]
               
                if footer_type == "login":
                    username = decrypted_data["data"].get("username", "")
                    password = decrypted_data["data"].get("password", "")
                    meta_data = decrypted_data["data"].get("meta_data", {})
                    
                    login_status = incCertAPI.login(username, password)
                    if login_status['status_code'] == 200:
                        meta_data["username"] = username
                        meta_data["password"] = password
                        response = {
                            "screen": "SCREEN_ONE",
                            "data": {
                                "reqd": True,
                                "meta_data": meta_data
                            }
                        }
                    else:
                        response = {
                                "screen": "LOGIN",
                                "data": {
                                    "reqd": True,
                                    "error": True,
                                    "error_message": "Invalid Credentials",
                                }
                            }
                       
                elif footer_type == "SCREEN_ONE":
                    meta_data = decrypted_data["data"].get("meta_data", {})
                    state_data = state
                    district = incCertAPI.getDistricts()
                    for key, value in decrypted_data["data"].items():
                        if key == "meta_data":
                            continue
                        meta_data[key] = value
                    if "photo_picker" in meta_data:
                        response = {
                            "screen": "SCREEN_TWO",
                            "data": {
                                "meta_data": meta_data,
                                "reqd": True,
                                "per_vill_reqd": True,
                                "pre_vill_reqd": True,
                                "all_per_state": state_data,
                                "all_pre_state": state_data,
                                "all_pre_state_init": "21_Odisha",
                                "all_pre_state_enabled": False,
                                "all_pre_district": district
                            }
                        }
                    else:
                        response = {
                            "screen": "SCREEN_ONE",
                            "data": {
                                "error": True,
                                "error_message": "Upload a picture"
                            }
                        }
           
                elif footer_type == "SCREEN_TWO":
                    meta_data = decrypted_data["data"]["meta_data"]
                    # district = incCertAPI.getDistricts()
                    for key, value in decrypted_data["data"].items():
                        if key == "meta_data":
                            continue
                        meta_data[key] = value
                    
                    
                    response = {
                        "screen": "SCREEN_THREE",
                        "data": {
                            "reqd": True,
                            "meta_data": meta_data,
                            "apply_to_office_init":[i['tehsil'] for i in income_tehsil if  meta_data.get("present_tehsil", "").split("_")[1].lower() in i['tehsil'].lower()][0] ,
                        }
                    }
                
                elif footer_type == "SCREEN_THREE":
                    meta_data = decrypted_data["data"]["meta_data"]
                    
                    for key, value in decrypted_data["data"].items():    
                        if key == "meta_data":
                            continue
                        meta_data[key] = value
                        
                        response = {
                        "screen": "SCREEN_FOUR",
                        "data": {
                            "reqd": True,
                            "meta_data": meta_data,
                            "document_name_other_visible": False,
                            "upload_type": "Document",
                            "button_activate": False,
                            "document_to_be_attached_visible": True,
                            "final_visible": False
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
 