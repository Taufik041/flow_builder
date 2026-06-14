# ruff: noqa
from fastapi import APIRouter, Body, Depends  # type: ignore
from fastapi.responses import PlainTextResponse  # type: ignore
from core.keys import PHONE_NUMBER_PRIVATE_KEY  # type: ignore
from utils.fb_utils import decrypt_request, encrypt_response  # type: ignore
from services import sebc_certificateApis  # type: ignore
from utils.helper_functions import get_base64_file  # type: ignore
from jsondata.LANDREG.message_ref import get_all_messages  # type: ignore
from datetime import datetime
import base64

sample_router = APIRouter()


@sample_router.post("/sample")
async def sample(body: dict = Body(...)):
    encrypt_flow_data_b64 = body["encrypted_flow_data"]
    encrypt_aes_key_b64 = body["encrypted_aes_key"]
    initial_vector_b64 = body["initial_vector"]
    sebcCertAPI = sebc_certificateApis.SebcCertificateAPI()  # api calls where required
    decrypted_data, aes_key, iv = decrypt_request(
        encrypt_flow_data_b64,
        encrypt_aes_key_b64,
        initial_vector_b64,
        PHONE_NUMBER_PRIVATE_KEY,
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
        else:
            if decrypted_data["data"] == {}:
                response = {
                    "screen": "LOGIN",
                    "data": {"reqd": True, "otp_sent": False, "meta_data": {}},
                }

            elif "trigger" in decrypted_data["data"]:
                trigger_type = decrypted_data["data"]["trigger"]

                if trigger_type == "get_otp":
                    meta_data = decrypted_data["data"].get("meta_data", {})
                    username = meta_data.get("username", "")
                    meta_data["username"] = username
                    # logic for sending otp goes here
                    response = {
                        "screen": decrypted_data["screen"],
                        "data": {
                            "error_message": get_all_messages(
                                "OTP_SENT", user_language
                            ),
                            "meta_data": meta_data,
                            "otp_sent": True,
                        },
                    }

                elif trigger_type == "photo_upload_trigger":
                    # TODO: Validate and convert photo to base64
                    # Expected: decrypted_data["data"]["photo_picker"] is a list with one item
                    # Steps a human should implement:
                    #   1. Get the file from photo_picker[0]
                    #   2. Convert to base64 using get_base64_file()
                    #   3. Check file size is >= 20KB
                    #   4. If valid: store base64 in meta_data["photo"] and enable footer
                    #   5. If invalid: return error, keep footer disabled

                    meta_data = decrypted_data["data"].get("meta_data", {})

                    # TODO: replace this block with real validation
                    photo_valid = False  # set True after successful validation
                    # meta_data["photo"] = base64_photo  # uncomment after validation

                    if not photo_valid:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "footer_enabled": False,
                                "error": True,
                                "error_message": get_all_messages(
                                    "PHOTO_ERROR", user_language
                                ),
                            },
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "footer_enabled": True,
                                "error": False,
                                "error_message": get_all_messages(
                                    "UPLOAD_SUCCESS", user_language
                                ),
                                "meta_data": meta_data,
                            },
                        }
                elif trigger_type == "salutation":
                    salutation = decrypted_data["data"]["salutation"]
                    meta_data = decrypted_data["data"].get("meta_data", {})
                    gender = sebcCertAPI.getGender(salutation)
                    marital_status = sebcCertAPI.getMaritalStatus(salutation)
                    response = {
                        "screen": decrypted_data["screen"],
                        "data": {
                            "gender": gender,
                            "marital_status": marital_status,
                            "meta_data": meta_data,
                        },
                    }

                elif trigger_type == "caste_search":
                    resp_data = {}
                    try:
                        caste = decrypted_data["data"]["caste"]
                        if len(caste) < 3:
                            resp_data["error"] = True
                            resp_data["error_message"] = get_all_messages(
                                "CASTE_ERROR_NOT_ENOUGH", user_language
                            )
                            raise Exception("length less than 3")
                        caste_visible = bool(caste)
                        caste_list = sebcCertAPI.getCaste()
                        show_d = []
                        for d in caste_list:
                            if caste.lower() in d["title"].lower():
                                show_d.append(d)
                        if not show_d:
                            resp_data["error"] = True
                            resp_data["error_message"] = get_all_messages(
                                "CASTE_ERROR", user_language
                            )
                            raise Exception("Caste not found")

                        resp_data["caste_visible"] = caste_visible
                        resp_data["caste_data"] = show_d
                        resp_data["caste_visible"] = True

                    except:
                        resp_data["error"] = True
                        resp_data["error_message"] = get_all_messages(
                            "CASTE_ERROR", user_language
                        )
                    response = {"screen": decrypted_data["screen"], "data": resp_data}

                elif trigger_type == "caste":
                    selected_caste = decrypted_data["data"].get("selected_caste", "")

                    if selected_caste == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "Resolution_No": [],
                            },
                        }
                    else:
                        res_no = sebcCertAPI.getResno(selected_caste)
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {"Resolution_No": res_no},
                        }
                elif trigger_type == "Resolution_No":
                    response = {"screen": decrypted_data["screen"], "data": {}}
                elif trigger_type == "present_district":
                    present_district = decrypted_data["data"]["present_district"]
                    response = {
                        "screen": decrypted_data["screen"],
                        "data": {
                            "all_pre_subdivision": [
                                {"id": "1", "title": "Subdivision 1"}
                            ],
                            "pre_dist_init": present_district,
                        },
                    }

                elif trigger_type == "present_subdivision":
                    # similar logic for tehsil, ri circle and village can be implemented like this
                    response = {"screen": decrypted_data["screen"], "data": {}}
                elif trigger_type == "present_terms":
                    present_terms = decrypted_data["data"].get("present_terms", "")

                    if present_terms == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "present_village_enabled": True,
                                "pre_vill_reqd": True,
                            },
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "present_village_enabled": False,
                                "pre_vill_reqd": False,
                            },
                        }
            elif "footer" in decrypted_data["data"]:
                footer_type = decrypted_data["data"]["footer"]

                if footer_type == "LOGIN":
                    meta_data = decrypted_data["data"].get("meta_data", {})
                    form = decrypted_data["data"].get("form", {})
                    meta_data.update(form)
                    # otp verification and login logic here
                    # if successful_login:
                    response = {
                        "screen": "PERSONAL_DETAILS",
                        "data": {
                            "reqd": True,
                            "error": True,
                            "error_message": get_all_messages(
                                "LOGIN_SUCCESS", user_language
                            ),
                        },
                    }
                    # if failed_login:
                    # response = {
                    #     "screen": decrypted_data["screen"],
                    #     "data": {
                    #         "reqd": True,
                    #         "error": True,
                    #         "error_message": get_all_messages("INVALID_OTP", user_language),
                    #     }
                    # }
                elif footer_type == "PERSONAL_DETAILS":
                    meta_data = decrypted_data["data"].get("meta_data", {})
                    form = decrypted_data["data"].get("form", {})
                    meta_data.update(form)

                    # notice we have same logic for photo validation and conversion in trigger upload and final1,
                    # this is a bug fix so we need do try conversion twice and save it
                    # we can create a separate function for that and call it in both places to avoid code repetition.
                    # I have kept it like this just for demonstration
                    if "photo_picker" in meta_data:
                        # same logic for photo validation and conversion from final1 to b64 goes here
                        response = {
                            "screen": "ADDRESS",
                            "data": {
                                "footer_enabled": True,
                                "meta_data": meta_data,
                                "all_pre_district": [
                                    {"id": "1", "title": "District 1"}
                                ],
                                "all_per_district": [
                                    {"id": "1", "title": "District 1"}
                                ],
                                "reqd": True,
                            },
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "error": True,
                                "error_message": "Upload a picture",
                            },
                        }
                elif footer_type == "ADDRESS":
                    meta_data = decrypted_data["data"]["meta_data"]
                    form = decrypted_data["data"]["form"]
                    meta_data.update(form)
                    response = {
                        "screen": "DOCUMENTS",
                        "data": {
                            "reqd": True,
                            "meta_data": meta_data,
                        },
                    }

    except Exception as e:
        import traceback

        traceback.print_exc()
        response = {
            "screen": decrypted_data["screen"] if "screen" in decrypted_data else "",
            "data": {"error": True, "error_message": "SOME ERROR OCCURED"},
        }

    encrypted_response = encrypt_response(response, aes_key, iv)
    return PlainTextResponse(content=encrypted_response, media_type="text/plain")
