# ruff: noqa
import base64
import traceback
from datetime import datetime

from core import get_db  # type: ignore
from core.keys import PHONE_NUMBER_PRIVATE_KEY  # type: ignore
from fastapi import APIRouter, Body, Depends  # type: ignore
from fastapi.responses import PlainTextResponse  # type: ignore
from jsondata.LANDREG.extra_data import sebc_tehsil  # type: ignore
from jsondata.LANDREG.message_ref import get_all_messages  # type: ignore
from jsondata.REVENUE.revenue_data import SEBC_SCREEN_MAPPER  # type: ignore
from models.flow_logs import FlowLogs  # type: ignore
from services.revenue import revenue_apis, revenue_db_data  # type: ignore
from utils.fb_utils import decrypt_request, encrypt_response  # type: ignore
from utils.helper_functions import get_base64_file  # type: ignore

sebc_router = APIRouter()


@sebc_router.post("/sebc")
async def sebc(body: dict = Body(...), db=Depends(get_db)):
    flowid = None

    encrypt_flow_data_b64 = body["encrypted_flow_data"]
    encrypt_aes_key_b64 = body["encrypted_aes_key"]
    initial_vector_b64 = body["initial_vector"]
    sebcCertAPI = revenue_db_data.RevenueDBData()
    revenue_api = revenue_apis.RevenueAPIS()
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
        flowid = None
    update = {"lastupdatedtime": datetime.now()}
    try:
        if decrypted_data["action"] == "ping":
            response = {"data": {"status": "active"}}
        else:
            if decrypted_data["data"] == {}:
                update.update(
                    {
                        "current": "FLOW_OPEN",
                        "meta_data": {
                            "msg": "USER HAS OPENED THE FLOW",
                            "type": "INFO",
                            "data": {},
                            "error": "",
                        },
                    }
                )
                response = {
                    "screen": "LOGIN",
                    "data": {"reqd": True, "otp_sent": False, "meta_data": {}},
                }

            elif "trigger" in decrypted_data["data"]:
                trigger_type: str = decrypted_data["data"]["trigger"]
                if trigger_type == "salutation":
                    salutation = decrypted_data["data"]["salutation"]
                    meta_data = decrypted_data["data"].get("meta_data", {})
                    gender = sebcCertAPI.getGender(salutation)
                    marital_status = sebcCertAPI.getMaritalStatus(salutation)
                    response = {
                        "screen": "SCREEN_ONE",
                        "data": {
                            "gender": gender,
                            "marital_status": marital_status,
                            "meta_data": meta_data,
                        },
                    }

                elif trigger_type == "get_otp":
                    username = decrypted_data["data"].get("username", "")
                    if username == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "otp_sent": True,
                                "error_message": get_all_messages(
                                    "USERNAME_ERROR", user_language
                                ),
                            },
                        }
                    else:
                        otp_response = revenue_api.get_otp(username)
                        if otp_response.get("status_code", 500) == 200:
                            response = {
                                "screen": decrypted_data["screen"],
                                "data": {
                                    "otp_sent": True,
                                    "error_message": get_all_messages(
                                        "OTP_SENT", user_language
                                    ),
                                },
                            }
                        else:
                            response = {
                                "screen": decrypted_data["screen"],
                                "data": {
                                    "otp_sent": False,
                                    "error_message": get_all_messages(
                                        "OTP_ERROR", user_language
                                    ),
                                },
                            }
                elif trigger_type == "final1":
                    # photo=decrypted_data["data"].get("photo", "")
                    try:
                        doc = decrypted_data["data"].get("photo_picker")
                        meta_data = decrypted_data["data"].get("meta_data", {})
                        if not doc:
                            photo = ""
                        else:
                            document = doc[0]
                            base64_doc = get_base64_file(document)
                            image_bytes = len(base64.b64decode(base64_doc))
                            size_kb = int(image_bytes / 1024)
                            if size_kb < 20:
                                raise Exception("size not correct")
                            photo = base64_doc
                            meta_data["photo_picker"] = photo
                    except:
                        if "photo_picker" not in decrypted_data["data"]:
                            photo = ""
                        else:
                            first_item = decrypted_data["data"]["photo_picker"][0]
                            cdn_url = first_item.get("cdn_url", "")
                            if cdn_url == "":
                                response = {
                                    "screen": decrypted_data["screen"],
                                    "data": {
                                        "footer_enabled": False,
                                        "error": True,
                                        "error_message": get_all_messages(
                                            "PHOTO_REQ", user_language
                                        ),
                                    },
                                }

                            elif (
                                cdn_url
                                == "EXAMPLE_DATA__CDN_URL_WILL_COME_IN_THIS_FIELD"
                            ):
                                photo = "ok"
                            else:
                                photo = ""
                    if not photo:
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
                                "error": True,
                                "error_message": get_all_messages(
                                    "UPLOAD_SUCCESS", user_language
                                ),
                                "meta_data": meta_data,
                            },
                        }

                elif trigger_type == "want_register":
                    response = {"screen": "REGISTRATION", "data": {"registered": False}}
                elif trigger_type == "register":
                    if (
                        "name" not in decrypted_data["data"]
                        or "email" not in decrypted_data["data"]
                        or "mobile" not in decrypted_data["data"]
                        or "age" not in decrypted_data["data"]
                    ):
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "registered": False,
                                "error_message": get_all_messages(
                                    "INFORMATION", user_language
                                ),
                            },
                        }
                    else:
                        name = decrypted_data["data"]["name"]
                        email = decrypted_data["data"]["email"]
                        mobile = decrypted_data["data"]["mobile"]
                        age = decrypted_data["data"]["age"]
                        reg_response = revenue_api.register(name, email, mobile, age)
                        if reg_response.get("status_code", 500) == 200:
                            response = {
                                "screen": decrypted_data["screen"],
                                "data": {
                                    "registered": True,
                                    "password_url": reg_response.get(
                                        "verificationLink", ""
                                    ),
                                },
                            }
                        else:
                            response = {
                                "screen": decrypted_data["screen"],
                                "data": {
                                    "registered": False,
                                    "error_message": reg_response["remarks"]
                                    if "remarks" in reg_response
                                    else get_all_messages(
                                        "REGISTRATION_ERROR", user_language
                                    ),
                                },
                            }

                elif trigger_type == "present_district":
                    present_district = decrypted_data["data"]["present_district"]
                    if present_district == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "pre_dist_init": "",
                                "pre_subdiv_init": "",
                                "pre_tehsil_init": "",
                                "pre_ri_circle_init": "",
                                "present_village_init": "",
                                "all_pre_subdivision": [],
                                "all_pre_tehsil": [],
                                "all_pre_ricircle": [],
                                "all_pre_village": [],
                            },
                        }
                    else:
                        sub_list = sebcCertAPI.getSubdivision(
                            int(present_district.split("_")[0])
                        )
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "all_pre_subdivision": sub_list,
                                "pre_dist_init": present_district,
                            },
                        }

                elif trigger_type == "present_subdivision":
                    present_subdivision = decrypted_data["data"]["present_subdivision"]
                    if present_subdivision == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "pre_subdiv_init": "",
                                "pre_tehsil_init": "",
                                "pre_ri_circle_init": "",
                                "present_village_init": "",
                                "all_pre_tehsil": [],
                                "all_pre_ricircle": [],
                                "all_pre_village": [],
                            },
                        }
                    else:
                        teh_list = sebcCertAPI.getTehsil(
                            int(present_subdivision.split("_")[0])
                        )
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "all_pre_tehsil": teh_list,
                                "pre_subdiv_init": present_subdivision,
                            },
                        }

                elif trigger_type == "present_tehsil":
                    present_tehsil = decrypted_data["data"]["present_tehsil"]
                    if present_tehsil == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "pre_tehsil_init": "",
                                "pre_ri_circle_init": "",
                                "present_village_init": "",
                                "all_pre_ricircle": [],
                                "all_pre_village": [],
                            },
                        }
                    else:
                        ri = sebcCertAPI.getRi(int(present_tehsil.split("_")[0]))
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "all_pre_ricircle": ri,
                                "pre_tehsil_init": present_tehsil,
                            },
                        }

                elif trigger_type == "present_ri_circle":
                    present_ri_circle = decrypted_data["data"]["present_ri_circle"]
                    village = sebcCertAPI.getVillage(
                        int(present_ri_circle.split("_")[0])
                    )
                    if present_ri_circle == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {"present_village_init": "", "all_pre_village": []},
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "all_pre_village": village,
                                "pre_ri_circle_init": present_ri_circle,
                            },
                        }

                elif trigger_type == "present_village":
                    present_village = decrypted_data["data"]["present_village"]
                    if present_village == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {"present_village_init": ""},
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {"present_village_init": present_village},
                        }

                elif trigger_type == "permanent_village":
                    permanent_village = decrypted_data["data"]["permanent_village"]
                    if permanent_village == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {"permanent_village_init": ""},
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {"permanent_village_init": permanent_village},
                        }

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

                elif trigger_type == "permanent_terms":
                    permanent_terms = decrypted_data["data"].get("permanent_terms", "")

                    if permanent_terms == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "permanent_village_enabled": True,
                                "per_vill_reqd": True,
                            },
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "permanent_village_enabled": False,
                                "per_vill_reqd": False,
                            },
                        }

                elif trigger_type == "permanent_state":
                    permanent_state = decrypted_data["data"]["permanent_state"]
                    if permanent_state == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {"all_per_district": []},
                        }
                    else:
                        district = sebcCertAPI.getDistricts()
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {"all_per_district": district},
                        }

                elif trigger_type == "permanent_district":
                    permanent_district = decrypted_data["data"]["permanent_district"]
                    if permanent_district == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "all_per_subdivision": [],
                                "per_dist_init": "",
                                "per_subdiv_init": "",
                                "per_tehsil_init": "",
                                "per_ri_circle_init": "",
                                "permanent_village_init": "",
                                "all_per_tehsil": [],
                                "all_per_ricircle": [],
                                "all_per_village": [],
                            },
                        }
                    else:
                        subdivision = sebcCertAPI.getSubdivision(
                            int(permanent_district.split("_")[0])
                        )
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "all_per_subdivision": subdivision,
                                "per_dist_init": permanent_district,
                                "per_subdiv_init": "",
                                "per_tehsil_init": "",
                                "per_ri_circle_init": "",
                                "all_per_tehsil": [],
                                "all_per_ricircle": [],
                                "all_per_village": [],
                                "permanent_village_init": "",
                            },
                        }
                elif trigger_type == "permanent_subdivision":
                    permanent_subdivision = decrypted_data["data"][
                        "permanent_subdivision"
                    ]
                    if permanent_subdivision == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "all_per_tehsil": [],
                                "all_per_ricircle": [],
                                "all_per_village": [],
                                "per_subdiv_init": "",
                                "per_tehsil_init": "",
                                "per_ri_circle_init": "",
                                "permanent_village_init": "",
                            },
                        }
                    else:
                        teh_list = sebcCertAPI.getTehsil(
                            int(permanent_subdivision.split("_")[0])
                        )
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "per_subdiv_init": permanent_subdivision,
                                "all_per_tehsil": teh_list,
                                "all_per_ricircle": [],
                                "all_per_village": [],
                                "per_tehsil_init": "",
                                "per_ri_circle_init": "",
                                "permanent_village_init": "",
                            },
                        }

                elif trigger_type == "permanent_tehsil":
                    permanent_tehsil = decrypted_data["data"]["permanent_tehsil"]
                    if permanent_tehsil == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "all_per_ricircle": [],
                                "all_per_village": [],
                                "per_ri_circle_init": "",
                                "per_tehsil_init": "",
                                "permanent_village_init": "",
                            },
                        }
                    else:
                        ri = sebcCertAPI.getRi(int(permanent_tehsil.split("_")[0]))
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "all_per_ricircle": ri,
                                "per_tehsil_init": permanent_tehsil,
                                "all_per_village": [],
                                "per_ri_circle_init": "",
                                "permanent_village_init": "",
                            },
                        }

                elif trigger_type == "permanent_ri_circle":
                    permanent_ri_circle = decrypted_data["data"]["permanent_ri_circle"]
                    if permanent_ri_circle == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "all_per_village": [],
                                "per_ri_circle_init": "",
                                "permanent_village_init": "",
                            },
                        }
                    else:
                        village = sebcCertAPI.getVillage(
                            int(permanent_ri_circle.split("_")[0])
                        )
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "all_per_village": village,
                                "per_ri_circle_init": permanent_ri_circle,
                                "permanent_village_init": "",
                            },
                        }
                elif trigger_type == "muncipalselected_p":
                    muncipalselected_p = decrypted_data["data"].get(
                        "muncipal_selected", ""
                    )
                    if muncipalselected_p == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipalselected_p_init": "",
                                "district3_init": "",
                                "muncipal_corporation": [],
                                "muncipality": [],
                                "muncipality_ward": [],
                                "NAC": [],
                                "NAC_WARD": [],
                                "muncipal_corporation_ward": [],
                                "pre_mw_init": "",
                                "pre_m_init": "",
                                "pre_mc_init": "",
                                "pre_mcw_init": "",
                                "pre_NAC_init": "",
                                "pre_NACW_init": "",
                            },
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipalselected_p_init": muncipalselected_p,
                                "muncipal_corporation": [],
                                "muncipality": [],
                                "muncipality_ward": [],
                                "NAC": [],
                                "district3_init": "",
                                "NAC_WARD": [],
                                "muncipal_corporation_ward": [],
                                "pre_mw_init": "",
                                "pre_m_init": "",
                                "pre_mc_init": "",
                                "pre_mcw_init": "",
                                "pre_NAC_init": "",
                                "pre_NACW_init": "",
                            },
                        }

                elif trigger_type == "selected_area":
                    area_selected = decrypted_data["data"].get("area_selected", "")
                    district = sebcCertAPI.get_district_add_urban()

                    unique_districts = {d["id"]: d for d in district}

                    dist = list(unique_districts.values())
                    for f in dist:
                        if f == {"id": "", "title": ""}:
                            dist.remove(f)

                    if area_selected == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "select_area_present_init": "",
                                "prelocaldis_visible": False,
                            },
                        }

                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipalselected_p_init": "",
                                "prelocaldis_visible": True,
                                "district3": dist,
                                "district3_init": "",
                                "present_block3_init": "",
                                "present_gp3_init": "",
                                "present_village3_init": "",
                                "select_area_present_init": area_selected,
                            },
                        }

                elif trigger_type == "muncipal_cor_p":
                    municipal_corp = decrypted_data["data"].get("muncipal", "")
                    muncipal_corporation_ward = (
                        sebcCertAPI.get_muncipal_corp_ward_add_urban(
                            str(municipal_corp)
                        )
                    )
                    unique_districts = {d["id"]: d for d in muncipal_corporation_ward}
                    m_corp_wa = list(unique_districts.values())
                    for f in m_corp_wa:
                        if f == {"id": "", "title": ""}:
                            m_corp_wa.remove(f)

                    if municipal_corp == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipal_corporation_ward": [],
                                "pre_mc_init": "",
                                "pre_mcw_init": "",
                            },
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipal_corporation_ward": m_corp_wa,
                                "pre_mc_init": municipal_corp,
                                "pre_mcw_init": "",
                            },
                        }

                elif trigger_type == "muncipal_cor_permanent":
                    municipal_corp = decrypted_data["data"].get("muncipal", "")
                    muncipal_corporation_ward = (
                        sebcCertAPI.get_muncipal_corp_ward_add_urban(
                            str(municipal_corp)
                        )
                    )
                    unique_districts = {d["id"]: d for d in muncipal_corporation_ward}
                    m_corp_wa = list(unique_districts.values())
                    for f in m_corp_wa:
                        if f == {"id": "", "title": ""}:
                            m_corp_wa.remove(f)

                    if municipal_corp == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipal_corporation_ward_permanent": [],
                                "per_mc_init": "",
                                "per_mcw_init": "",
                            },
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipal_corporation_ward_permanent": m_corp_wa,
                                "per_mc_init": municipal_corp,
                                "per_mcw_init": "",
                            },
                        }

                elif trigger_type == "muncipality_p":
                    selected_muncipality = decrypted_data["data"].get("muncipality", "")
                    municipality_ward = sebcCertAPI.get_municipality_ward_add_urban(
                        selected_muncipality
                    )
                    unique_districts = {d["id"]: d for d in municipality_ward}
                    m_wa = list(unique_districts.values())
                    for f in m_wa:
                        if f == {"id": "", "title": ""}:
                            m_wa.remove(f)
                    if selected_muncipality == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipal_ward": [],
                                "pre_mw_init": "",
                                "pre_m_init": "",
                            },
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipal_ward": m_wa,
                                "pre_mw_init": "",
                                "pre_m_init": selected_muncipality,
                            },
                        }

                elif trigger_type in ["pre_mcw", "pre_mw", "pre_NACW"]:
                    pre_mcw = decrypted_data["data"].get("pre_mcw", "")
                    pre_mw = decrypted_data["data"].get("pre_mw", "")
                    pre_NACW = decrypted_data["data"].get("pre_NACW", "")
                    response = {
                        "screen": decrypted_data["screen"],
                        "data": {
                            "pre_mcw_init": pre_mcw,
                            "pre_mw_init": pre_mw,
                            "pre_NACW_init": pre_NACW,
                        },
                    }

                elif trigger_type in ["per_mcw", "per_mw", "per_NACW"]:
                    per_mcw = decrypted_data["data"].get("per_mcw", "")
                    per_mw = decrypted_data["data"].get("per_mw", "")
                    per_NACW = decrypted_data["data"].get("per_NACW", "")
                    response = {
                        "screen": decrypted_data["screen"],
                        "data": {
                            "per_mcw_init": per_mcw,
                            "per_mw_init": per_mw,
                            "per_NACW_init": per_NACW,
                        },
                    }

                elif trigger_type == "muncipality_permanent":
                    selected_muncipality = decrypted_data["data"].get("muncipality", "")
                    municipality_ward = sebcCertAPI.get_municipality_ward_add_urban(
                        selected_muncipality
                    )
                    unique_districts = {d["id"]: d for d in municipality_ward}
                    m_wa = list(unique_districts.values())
                    for f in m_wa:
                        if f == {"id": "", "title": ""}:
                            m_wa.remove(f)
                    if selected_muncipality == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipal_ward_permanent": [],
                                "per_m_init": "",
                                "per_mw_init": "",
                            },
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipal_ward_permanent": m_wa,
                                "per_m_init": selected_muncipality,
                                "per_mw_init": "",
                            },
                        }

                elif trigger_type == "NAC_p":
                    selected_NAC = decrypted_data["data"].get("NAC", "")
                    nac_ward = sebcCertAPI.get_nac_ward_add_urban(selected_NAC)
                    unique_districts = {d["id"]: d for d in nac_ward}
                    nac_wa = list(unique_districts.values())
                    for f in nac_wa:
                        if f == {"id": "", "title": ""}:
                            nac_wa.remove(f)
                    if selected_NAC == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "NAC_WARD": [],
                                "pre_NAC_init": "",
                                "pre_NACW_init": "",
                            },
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "NAC_WARD": nac_wa,
                                "pre_NAC_init": selected_NAC,
                                "pre_NACW_init": "",
                            },
                        }

                elif trigger_type == "NAC_permanent":
                    selected_NAC = decrypted_data["data"].get("NAC", "")
                    nac_ward = sebcCertAPI.get_nac_ward_add_urban(selected_NAC)
                    unique_districts = {d["id"]: d for d in nac_ward}
                    nac_wa = list(unique_districts.values())
                    for f in nac_wa:
                        if f == {"id": "", "title": ""}:
                            nac_wa.remove(f)
                    if selected_NAC == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "NAC_WARD_permanent": [],
                                "per_NAC_init": "",
                                "per_NACW_init": "",
                            },
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "NAC_WARD_permanent": nac_wa,
                                "per_NAC_init": selected_NAC,
                                "per_NACW_init": "",
                            },
                        }

                elif trigger_type == "district3":
                    district = decrypted_data["data"].get("district", "")
                    if district == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "block3": [],
                                "gp3": [],
                                "village3": [],
                                "muncipal_corporation": [],
                                "muncipality": [],
                                "district3_init": "",
                                "muncipality_ward": [],
                                "NAC": [],
                                "NAC_WARD": [],
                                "muncipal_corporation_ward": [],
                                "pre_mw_init": "",
                                "pre_m_init": "",
                                "pre_mc_init": "",
                                "pre_mcw_init": "",
                                "pre_NAC_init": "",
                                "pre_NACW_init": "",
                                "present_block3_init": "",
                                "present_gp3_init": "",
                                "present_village3_init": "",
                            },
                        }
                    else:
                        municipal_corp = sebcCertAPI.get_muncipal_corp_add_urban(
                            district
                        )
                        municipality = sebcCertAPI.get_municipality_add_urban(district)
                        nac = sebcCertAPI.get_nac_add_urban(district)
                        block = sebcCertAPI.getBlock(district)

                        unique_districts = {d["id"]: d for d in municipal_corp}
                        m_corp = list(unique_districts.values())
                        for f in m_corp:
                            if f == {"id": "", "title": ""}:
                                m_corp.remove(f)

                        unique_districts2 = {d["id"]: d for d in municipality}
                        m = list(unique_districts2.values())
                        for f in m:
                            if f == {"id": "", "title": ""}:
                                m.remove(f)

                        unique_districts3 = {d["id"]: d for d in nac}
                        n = list(unique_districts3.values())
                        for f in n:
                            if f == {"id": "", "title": ""}:
                                n.remove(f)

                        unique_districts4 = {d["id"]: d for d in block}
                        b = list(unique_districts4.values())
                        for f in b:
                            if f == {"id": "", "title": ""}:
                                b.remove(f)
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "block3": b,
                                "muncipal_corporation": m_corp,
                                "muncipality": m,
                                "district3_init": district,
                                "muncipality_ward": [],
                                "NAC": n,
                                "NAC_WARD": [],
                                "muncipal_corporation_ward": [],
                                "pre_mw_init": "",
                                "pre_m_init": "",
                                "pre_mc_init": "",
                                "pre_mcw_init": "",
                                "pre_NAC_init": "",
                                "pre_NACW_init": "",
                                "gp3": [],
                                "present_gp3_init": "",
                                "village3": [],
                                "present_village3_init": "",
                            },
                        }

                elif trigger_type == "block3":
                    selected_rural_block = decrypted_data["data"].get("block")
                    if selected_rural_block == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "gp3": [],
                                "present_gp3_init": "",
                                "present_block3_init": "",
                                "present_village3_init": "",
                                "village3": [],
                            },
                        }
                    else:
                        gp3 = sebcCertAPI.getGp(selected_rural_block)
                        unique_districts = {d["id"]: d for d in gp3}
                        g = list(unique_districts.values())
                        for f in g:
                            if f == {"id": "", "title": ""}:
                                g.remove(f)

                            response = {
                                "screen": decrypted_data["screen"],
                                "data": {
                                    "gp3": g,
                                    "present_block3_init": selected_rural_block,
                                    "present_gp3_init": "",
                                    "present_village3_init": "",
                                    "village3": [],
                                },
                            }
                elif trigger_type == "gp3":
                    selected_rural_gp = decrypted_data["data"].get("gp")
                    if selected_rural_gp == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "village3": [],
                                "present_village3_init": "",
                                "present_gp3_init": "",
                            },
                        }
                    else:
                        village3 = sebcCertAPI.getVillagebyGp(selected_rural_gp)
                        unique_districts = {d["id"]: d for d in village3}
                        v3 = list(unique_districts.values())
                        for f in v3:
                            if f == {"id": "", "title": ""}:
                                v3.remove(f)

                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "village3": v3,
                                "present_gp3_init": selected_rural_gp,
                            },
                        }

                elif trigger_type == "select_area_permanent":
                    area_selected = decrypted_data["data"].get("area_selected", "")
                    district = sebcCertAPI.get_district_add_urban()

                    unique_districts = {d["id"]: d for d in district}

                    dist = list(unique_districts.values())
                    for f in dist:
                        if f == {"id": "", "title": ""}:
                            dist.remove(f)

                    if area_selected == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "select_area_permanent_init": "",
                                "district1_init": "",
                                "perlocaldis_visible": False,
                            },
                        }

                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "select_muncipal_permanent_init": "",
                                "perlocaldis_visible": True,
                                "district1": dist,
                                "district1_init": "",
                                "permanent_block3_init": "",
                                "permanent_gp3_init": "",
                                "permanent_village3_init": "",
                                "select_area_permanent_init": area_selected,
                            },
                        }

                elif trigger_type == "muncipalselected_permanent":
                    muncipal_permanent = decrypted_data["data"].get(
                        "muncipal_selected", ""
                    )
                    if muncipal_permanent == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipal_corporation_permanent": [],
                                "muncipal_corporation_ward_permanent": [],
                                "muncipality_permanent": [],
                                "muncipality_ward_permanent": [],
                                "NAC_permanent": [],
                                "NAC_WARD_permanent": [],
                                "district1_init": "",
                                "select_muncipal_permanent_init": "",
                                "per_mw_init": "",
                                "per_m_init": "",
                                "per_mc_init": "",
                                "per_mcw_init": "",
                                "per_NAC_init": "",
                                "per_NACW_init": "",
                            },
                        }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipal_corporation_permanent": [],
                                "muncipal_corporation_ward_permanent": [],
                                "muncipality_permanent": [],
                                "muncipality_ward_permanent": [],
                                "NAC_permanent": [],
                                "NAC_WARD_permanent": [],
                                "district1_init": "",
                                "select_muncipal_permanent_init": muncipal_permanent,
                                "per_mw_init": "",
                                "per_m_init": "",
                                "per_mc_init": "",
                                "per_mcw_init": "",
                                "per_NAC_init": "",
                                "per_NACW_init": "",
                            },
                        }

                elif trigger_type == "district1_permanent":
                    district = decrypted_data["data"].get("District1", "")
                    if district == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipal_corporation_permanent": [],
                                "muncipal_corporation_ward_permanent": [],
                                "muncipality_permanent": [],
                                "district1_init": "",
                                "muncipality_ward_permanent": [],
                                "NAC_permanent": [],
                                "NAC_WARD_permanent": [],
                                "per_mw_init": "",
                                "per_m_init": "",
                                "per_mc_init": "",
                                "per_mcw_init": "",
                                "per_NAC_init": "",
                                "per_NACW_init": "",
                                "block3_permanent": [],
                                "permanent_block3_init": "",
                                "permanent_gp3_init": "",
                                "gp3_permanent": [],
                                "permanent_village3_init": "",
                                "village3_permanent": [],
                            },
                        }
                    else:
                        municipal_corp = sebcCertAPI.get_muncipal_corp_add_urban(
                            district
                        )
                        municipality = sebcCertAPI.get_municipality_add_urban(district)
                        nac = sebcCertAPI.get_nac_add_urban(district)
                        block = sebcCertAPI.getBlock(district)

                        unique_districts = {d["id"]: d for d in municipal_corp}
                        m_corp = list(unique_districts.values())
                        for f in m_corp:
                            if f == {"id": "", "title": ""}:
                                m_corp.remove(f)

                        unique_districts2 = {d["id"]: d for d in municipality}
                        m = list(unique_districts2.values())
                        for f in m:
                            if f == {"id": "", "title": ""}:
                                m.remove(f)

                        unique_districts3 = {d["id"]: d for d in nac}
                        n = list(unique_districts3.values())
                        for f in n:
                            if f == {"id": "", "title": ""}:
                                n.remove(f)

                        unique_districts4 = {d["id"]: d for d in block}
                        b = list(unique_districts4.values())
                        for f in b:
                            if f == {"id": "", "title": ""}:
                                b.remove(f)
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "muncipal_corporation_permanent": m_corp,
                                "muncipal_corporation_ward_permanent": [],
                                "muncipality_permanent": m,
                                "district1_init": district,
                                "muncipality_ward_permanent": [],
                                "NAC_permanent": n,
                                "NAC_WARD_permanent": [],
                                "per_mw_init": "",
                                "per_m_init": "",
                                "per_mc_init": "",
                                "per_mcw_init": "",
                                "per_NAC_init": "",
                                "per_NACW_init": "",
                                "block3_permanent": b,
                                "permanent_block3_init": "",
                                "permanent_gp3_init": "",
                                "gp3_permanent": [],
                                "permanent_village3_init": "",
                                "village3_permanent": [],
                            },
                        }
                elif trigger_type == "block3_permanent":
                    block = decrypted_data["data"].get("block", "")

                    if block == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "gp3_permanent": [],
                                "village3_permanent": [],
                                "permanent_gp3_init": "",
                                "permanent_block3_init": "",
                                "permanent_village3_init": "",
                            },
                        }
                    else:
                        gp = sebcCertAPI.getGp(block)
                        unique_districts = {d["id"]: d for d in gp}
                        g = list(unique_districts.values())
                        for f in g:
                            if f == {"id": "", "title": ""}:
                                g.remove(f)
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "gp3_permanent": g,
                                "permanent_block3_init": block,
                                "village3_permanent": [],
                                "permanent_village3_init": "",
                            },
                        }
                elif trigger_type == "gp3_permanent":
                    selected_rural_gp = decrypted_data["data"].get("gp", "")
                    if selected_rural_gp == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "village3_permanent": [],
                                "permanent_village3_init": "",
                                "permanent_gp3_init": "",
                            },
                        }
                    else:
                        village3 = sebcCertAPI.getVillagebyGp(selected_rural_gp)
                        unique_districts = {d["id"]: d for d in village3}
                        v3 = list(unique_districts.values())
                        for f in v3:
                            if f == {"id": "", "title": ""}:
                                v3.remove(f)

                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "village3_permanent": village3,
                                "permanent_gp3_init": selected_rural_gp,
                            },
                        }

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

                elif trigger_type == "caste_search":
                    resp_data = {}
                    try:
                        caste = decrypted_data["data"]["caste"]
                        # print("caste", caste)
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

                elif trigger_type == "Resolution_No":
                    selected_resolution_no = decrypted_data["data"][
                        "selected_Resolution_No"
                    ]
                    if selected_resolution_no == "":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "Resolution_Date": [],
                            },
                        }
                    else:
                        res_date = sebcCertAPI.getResdate(selected_resolution_no)
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {"Resolution_Date": res_date},
                        }

                elif trigger_type == "Resolution_Date":
                    decrypted_data["data"].get("selected_Resolution_Date", "")
                    response = {"screen": decrypted_data["screen"], "data": {}}

                elif trigger_type == "upload":
                    document_name_other_visible = False
                    DOC_MAP = {
                        "Identity_Proof": "copy_of_ROR",
                        "copy_of_ROR": "Land_Pass_Book",
                        "Land_Pass_Book": "Self_Declaration",
                        "Self_Declaration": "Other",
                    }
                    meta_data = decrypted_data["data"]["meta_data"]
                    for key, value in decrypted_data["data"].items():
                        if key == "meta_data":
                            continue
                        meta_data[key] = value

                    upload_type = decrypted_data["data"].get("upload_type", "")
                    Identity_Proof = decrypted_data["data"].get("Identity_Proof", "")
                    copy_of_ROR = decrypted_data["data"].get("copy_of_ROR", "")
                    Land_Pass_Book = decrypted_data["data"].get("Land_Pass_Book", "")
                    Self_Declaration = decrypted_data["data"].get(
                        "Self_Declaration", ""
                    )
                    Other = decrypted_data["data"].get("Other", "")
                    data = ""
                    if upload_type == "Identity_Proof":
                        cdn_url = (
                            Identity_Proof[0].get("cdn_url", "")
                            if Identity_Proof
                            else ""
                        )
                        if (
                            not Identity_Proof
                            or cdn_url
                            == "EXAMPLE_DATA__CDN_URL_WILL_COME_IN_THIS_FIELD"
                        ):
                            data = "fail"
                        else:
                            meta_data[upload_type] = Identity_Proof
                        document_name_other_visible = False

                    elif upload_type == "copy_of_ROR":
                        cdn_url = (
                            copy_of_ROR[0].get("cdn_url", "") if copy_of_ROR else ""
                        )
                        if (
                            not copy_of_ROR
                            or cdn_url
                            == "EXAMPLE_DATA__CDN_URL_WILL_COME_IN_THIS_FIELD"
                        ):
                            data = "fail"
                        else:
                            meta_data[upload_type] = copy_of_ROR
                        document_name_other_visible = False

                    elif upload_type == "Land_Pass_Book":
                        cdn_url = (
                            Land_Pass_Book[0].get("cdn_url", "")
                            if Land_Pass_Book
                            else ""
                        )
                        if (
                            not Land_Pass_Book
                            or cdn_url
                            == "EXAMPLE_DATA__CDN_URL_WILL_COME_IN_THIS_FIELD"
                        ):
                            data = "fail"
                        else:
                            meta_data[upload_type] = Land_Pass_Book
                        document_name_other_visible = False

                    elif upload_type == "Self_Declaration":
                        cdn_url = (
                            Self_Declaration[0].get("cdn_url", "")
                            if Self_Declaration
                            else ""
                        )
                        if (
                            not Self_Declaration
                            or cdn_url
                            == "EXAMPLE_DATA__CDN_URL_WILL_COME_IN_THIS_FIELD"
                        ):
                            data = "fail"
                        else:
                            meta_data[upload_type] = Self_Declaration
                        document_name_other_visible = True

                    elif upload_type == "Other":
                        document_name_other = decrypted_data["data"].get(
                            "document_name_other", ""
                        )
                        cdn_url = Other[0].get("cdn_url", "") if Other else ""
                        if (
                            not Other
                            or cdn_url
                            == "EXAMPLE_DATA__CDN_URL_WILL_COME_IN_THIS_FIELD"
                        ):
                            data = "fail"
                        else:
                            meta_data[document_name_other] = Other
                        document_name_other_visible = False

                    if data == "fail":
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "error": True,
                                "error_message": get_all_messages(
                                    "UPLOAD_REQUIRED", user_language
                                ),
                            },
                        }
                    elif upload_type in [
                        "Identity_Proof",
                        "copy_of_ROR",
                        "Land_Pass_Book",
                        "Self_Declaration",
                    ]:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "reqd": True,
                                "meta_data": meta_data,
                                "document_name_other_visible": document_name_other_visible,
                                "upload_type": DOC_MAP[upload_type],
                                "button_activate": True,
                                "upload_show": True,
                                "document_to_be_attached_visible": False,
                                "skip_visible": True,
                            },
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
                                },
                            }
                        else:
                            response = {
                                "screen": decrypted_data["screen"],
                                "data": {
                                    "error": True,
                                    "error_message": get_all_messages(
                                        "UPLOAD_NAME", user_language
                                    ),
                                },
                            }
                    else:
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "error": True,
                                "error_message": get_all_messages(
                                    "UPLOAD_REQUIRED", user_language
                                ),
                            },
                        }

            elif "footer" in decrypted_data["data"]:
                footer_type = decrypted_data["data"]["footer"]
                log_message = f"USER CLICKED ON THE {footer_type.upper()} BUTTON"
                log_info = "INFO"
                log_error = ""
                if footer_type == "login":
                    username = decrypted_data["data"].get("username", "")
                    OTP_data = decrypted_data["data"].get("OTP", "")
                    meta_data = decrypted_data["data"].get("meta_data", {})
                    login_status = revenue_api.login(
                        username, OTP_data, client_id="292425"
                    )
                    if login_status.get("status_code", 500) == 200:
                        meta_data["username"] = username
                        meta_data["OTP"] = OTP_data
                        meta_data["token_for_submit"] = login_status["token"]
                        meta_data["reference_no"] = login_status["reference_no"]
                        log_message = "USER LOGGED IN SUCCESSFULLY"
                        log_info = "INFO"
                        log_error = ""
                        response = {
                            "screen": "SCREEN_ONE",
                            "data": {
                                "reqd": True,
                                "meta_data": meta_data,
                                "footer_enabled": False,
                            },
                        }
                    elif login_status.get("status_code", 500) == 400:
                        log_message = "USER LOGIN FAILED"
                        log_info = "USER_ERROR"
                        log_error = "Invalid credentials or OTP limit exceeded"

                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "reqd": True,
                                "error": True,
                                "error_message": get_all_messages(
                                    "INVALID_CRED", user_language
                                ),
                            },
                        }
                    elif login_status.get("status_code", 500) == 500:
                        log_message = login_status.get("error", "LOGIN API failed")
                        log_info = "API_ERROR"
                        log_error = login_status.get(
                            "raw_response", traceback.format_exc()
                        )

                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "reqd": True,
                                "error": True,
                                "error_message": get_all_messages(
                                    "ERROR_IN_API", user_language
                                ),
                            },
                        }
                    else:
                        log_message = "USER LOGIN FAILED"
                        log_info = "API_ERROR"
                        log_error = traceback.format_exc()
                        response = {
                            "screen": decrypted_data["screen"],
                            "data": {
                                "reqd": True,
                                "error": True,
                                "error_message": get_all_messages(
                                    "ERROR_IN_API", user_language
                                ),
                            },
                        }

                elif footer_type == "SCREEN_ONE":
                    meta_data = decrypted_data["data"].get("meta_data", {})
                    state_data = sebcCertAPI.getState()
                    district = sebcCertAPI.getDistricts()
                    for key, value in decrypted_data["data"].items():
                        if key == "meta_data":
                            continue
                        meta_data[key] = value

                    if "applicantphoto" in meta_data:
                        try:
                            doc = decrypted_data["data"].get("applicantphoto")
                            meta_data = decrypted_data["data"].get("meta_data", {})
                            document = doc[0]
                            base64_doc = get_base64_file(document)
                            image_bytes = len(base64.b64decode(base64_doc))
                            size_kb = int(image_bytes / 1024)
                            if size_kb < 20:
                                raise Exception("size not correct")
                            photo = base64_doc
                            meta_data["photo_picker"] = photo
                        except:
                            first_item = decrypted_data["data"]["applicantphoto"][0]
                            cdn_url = first_item.get("cdn_url", "")
                            if cdn_url == "":
                                response = {
                                    "screen": decrypted_data["screen"],
                                    "data": {
                                        "footer_enabled": False,
                                        "error": True,
                                        "error_message": get_all_messages(
                                            "PHOTO_REQ", user_language
                                        ),
                                    },
                                }

                            elif (
                                cdn_url
                                == "EXAMPLE_DATA__CDN_URL_WILL_COME_IN_THIS_FIELD"
                            ):
                                photo = "ok"
                            else:
                                photo = ""
                        if not photo:
                            log_message = "PHOTO UPLOAD FAILED"
                            log_info = "USER_ERROR"
                            log_error = "Photo should be between 20KB and 200KB"
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
                            log_message = (
                                f"{SEBC_SCREEN_MAPPER.get(footer_type, '')} COMPLETED"
                            )
                            log_info = "INFO"
                            log_error = ""
                            response = {
                                "screen": "SCREEN_TWO",
                                "data": {
                                    "footer_enabled": True,
                                    "meta_data": meta_data,
                                    "reqd": True,
                                    "per_vill_reqd": True,
                                    "pre_vill_reqd": True,
                                    "all_per_state": state_data,
                                    "all_pre_state": state_data,
                                    "all_pre_state_init": "21_Odisha",
                                    "all_pre_state_enabled": False,
                                    "all_pre_district": district,
                                    "district1": district,
                                    "all_per_district": district,
                                    "perlocaldis_visible": False,
                                    "prelocaldis_visible": False,
                                    "select_area_present_init": "",
                                    "select_area_permanent_init": "",
                                    "current_date": datetime.now().strftime("%Y-%m-%d"),
                                },
                            }
                    else:
                        log_message = "PHOTO UPLOAD FAILED"
                        log_info = "USER_ERROR"
                        log_error = "Photo should be between 20KB and 200KB"
                        response = {
                            "screen": "SCREEN_ONE",
                            "data": {
                                "error": True,
                                "error_message": "Upload a picture",
                            },
                        }

                elif footer_type == "SCREEN_TWO":
                    meta_data = decrypted_data["data"]["meta_data"]
                    # district = sebcCertAPI.getDistricts()
                    for key, value in decrypted_data["data"].items():
                        if key == "meta_data":
                            continue
                        meta_data[key] = value
                    log_message = f"{SEBC_SCREEN_MAPPER.get(footer_type, '')} COMPLETED"
                    log_info = "INFO"
                    log_error = ""
                    response = {
                        "screen": "SCREEN_THREE",
                        "data": {
                            "reqd": True,
                            "current_date": datetime.now().strftime("%Y-%m-%d"),
                            "meta_data": meta_data,
                            "apply_to_office_init": [
                                i["tehsil"]
                                for i in sebc_tehsil
                                if meta_data.get("presenttehasil", "")
                                .split("_")[1]
                                .lower()
                                in i["tehsil"].lower()
                            ][0],
                        },
                    }

                elif footer_type == "SCREEN_THREE":
                    meta_data = decrypted_data["data"]["meta_data"]

                    for key, value in decrypted_data["data"].items():
                        if key == "meta_data":
                            continue
                        meta_data[key] = value

                    if meta_data.get("constipost") == "1":
                        father_mother = meta_data.get(
                            "selectfathermotherforconstipost", ""
                        )
                        if father_mother == "2":
                            meta_data["parservicecategory"] = meta_data.get(
                                "service_category", ""
                            )
                            meta_data["pradetailsofservice"] = meta_data.get(
                                "detailsof_service", ""
                            )
                        elif father_mother == "1":
                            meta_data["servicecategory"] = meta_data.get(
                                "service_category", ""
                            )
                            meta_data["detailsofservice"] = meta_data.get(
                                "detailsof_service", ""
                            )

                    if meta_data.get("govtserv") == "1":
                        father_mother = meta_data.get(
                            "selectfathermotherforgovtpost", ""
                        )
                        if father_mother == "1":
                            meta_data["proservice"] = meta_data.get("ser", "")
                            meta_data["prodesig"] = meta_data.get("des", "")
                            meta_data["proscalepay"] = meta_data.get("scale_pay", "")
                            meta_data["prodateofapptothepo"] = meta_data.get(
                                "date_of_appointment", ""
                            )
                            meta_data["proageatthetimetothepo"] = meta_data.get(
                                "age_at_promotion", ""
                            )
                        elif father_mother == "2":
                            meta_data["service"] = meta_data.get("ser", "")
                            meta_data["desig"] = meta_data.get("des", "")
                            meta_data["scalepay"] = meta_data.get("scale_pay", "")
                            meta_data["dateofapptothepo"] = meta_data.get(
                                "date_of_appointment", ""
                            )
                            meta_data["ageatthetimetothepo"] = meta_data.get(
                                "age_at_promotion", ""
                            )

                    if meta_data.get("empofinterorg") == "1":
                        father_mother = meta_data.get("selectforempofinterorg", "")

                        if father_mother == "1":
                            meta_data["pronameoforg"] = meta_data.get(
                                "name_of_organization", ""
                            )
                            meta_data["prodesign"] = meta_data.get(
                                "designation_international_organization", ""
                            )
                            meta_data["properiodofservfrom"] = meta_data.get(
                                "period_service_from", ""
                            )
                            meta_data["properiodofservto"] = meta_data.get(
                                "period_service_to", ""
                            )

                        elif father_mother == "2":
                            meta_data["nameoforg"] = meta_data.get(
                                "name_of_organization", ""
                            )
                            meta_data["design"] = meta_data.get(
                                "designation_international_organization", ""
                            )
                            meta_data["periodofservfrom"] = meta_data.get(
                                "period_service_from", ""
                            )
                            meta_data["periodofservto"] = meta_data.get(
                                "period_service_to", ""
                            )

                    if meta_data.get("deathperincap") == "1":
                        father_mother = meta_data.get(
                            "selectfatmotdeathhperincapputanoffoutofser", ""
                        )

                        if father_mother == "1":
                            meta_data["prodateofdeathperincap"] = meta_data.get(
                                "date_of_death_permanent_capacitation", ""
                            )
                            meta_data["prodetofperincap"] = meta_data.get(
                                "details_permanent_in_capacitation", ""
                            )

                        elif father_mother == "2":
                            meta_data["dateofdeathperincap"] = meta_data.get(
                                "date_of_death_permanent_capacitation", ""
                            )
                            meta_data["detofperincap"] = meta_data.get(
                                "details_permanent_in_capacitation", ""
                            )

                    if meta_data.get("empinpublicsectrunder") == "1":
                        father_mother = meta_data.get("seforempinpublicsectorunder", "")

                        if father_mother == "1":
                            meta_data["pronameoforganization"] = meta_data.get(
                                "name_of_organization1", ""
                            )
                            meta_data["prodesignation"] = meta_data.get(
                                "designation_psu", ""
                            )
                            meta_data["prodateofapptothepost"] = meta_data.get(
                                "date_appointment_post", ""
                            )
                            meta_data["proannualincome"] = meta_data.get(
                                "annual_income", ""
                            )

                        elif father_mother == "2":
                            meta_data["nameoforganization"] = meta_data.get(
                                "name_of_organization1", ""
                            )
                            meta_data["designation"] = meta_data.get(
                                "designation_psu", ""
                            )
                            meta_data["dateofapptothepost"] = meta_data.get(
                                "date_appointment_post", ""
                            )
                            meta_data["annualincome"] = meta_data.get(
                                "annual_income", ""
                            )

                    if meta_data.get("armedforincludingparamilfor") == "1":
                        father_mother = meta_data.get(
                            "selectfatmotforarmedforcesincludingparmilfor", ""
                        )

                        if father_mother == "1":
                            meta_data["prodesignati"] = meta_data.get(
                                "designation_afp", ""
                            )
                            meta_data["proscaleofpayincluclassifany"] = meta_data.get(
                                "scale_of_pay_classification", ""
                            )

                        elif father_mother == "2":
                            meta_data["designati"] = meta_data.get(
                                "designation_afp", ""
                            )
                            meta_data["scaleofpayincluclassifany"] = meta_data.get(
                                "scale_of_pay_classification", ""
                            )

                    if meta_data.get("professionalclass") == "1":
                        father_mother = meta_data.get(
                            "selectfathermotherforprofclass", ""
                        )

                        if father_mother == "1":
                            meta_data["proapploccupprof"] = meta_data.get(
                                "applicants_occupation_profession", ""
                            )

                        elif father_mother == "2":
                            meta_data["apploccupprof"] = meta_data.get(
                                "applicants_occupation_profession", ""
                            )
                    check_data = {
                        "scalepay": {"en": "scale pay", "od": "ସ୍କେଲ ପେ"},
                        "proscalepay": {"en": "scale pay", "od": "ସ୍କେଲ ପେ"},
                        "proageatthetimetothepo": {
                            "en": "age at the time to the post",
                            "od": "ପୋଷ୍ଟରେ ଥିବା ସମୟରେ ବୟସ",
                        },
                        "ageatthetimetothepo": {
                            "en": "age at the time to the post",
                            "od": "ପୋଷ୍ଟରେ ଥିବା ସମୟରେ ବୟସ",
                        },
                        "proannualincome": {"en": "annual income", "od": "ବାର୍ଷିକ ଆୟ"},
                        "annualincome": {"en": "annual income", "od": "ବାର୍ଷିକ ଆୟ"},
                    }
                    check = list(check_data.keys())
                    d = ""
                    f = ""
                    for c in check:
                        if c in meta_data:
                            if float(meta_data[c]) < 1:
                                d = "TEXT"
                                f = c
                                break
                            d = ""
                    if d == "TEXT":
                        log_message = f"{get_all_messages('MIN_VALUE_CHECK', 'EN').replace('~', check_data[f]['en'])}"
                        log_info = "USER_ERROR"
                        log_error = f"{get_all_messages('MIN_VALUE_CHECK', 'EN').replace('~', check_data[f]['en'])}"
                        response = {
                            "screen": "SCREEN_THREE",
                            "data": {
                                "error": True,
                                "error_message": get_all_messages(
                                    "MIN_VALUE_CHECK", user_language
                                ).replace("~", check_data[f][user_language]),
                            },
                        }
                    else:
                        log_message = (
                            f"{SEBC_SCREEN_MAPPER.get(footer_type, '')} COMPLETED"
                        )
                        log_info = "INFO"
                        log_error = ""
                        response = {
                            "screen": "SCREEN_FOUR",
                            "data": {
                                "reqd": True,
                                "meta_data": meta_data,
                                "current_date": datetime.now().strftime("%Y-%m-%d"),
                            },
                        }

                elif footer_type == "SCREEN_FOUR":
                    meta_data = decrypted_data["data"]["meta_data"]
                    for key, value in decrypted_data["data"].items():
                        if key == "meta_data":
                            continue
                        meta_data[key] = value

                    if (
                        meta_data.get("agrilandholdingownedbymotfatminorchildren")
                        == "1"
                    ):
                        father_mother = meta_data.get(
                            "sefatmotforagricultandholdiownedbymotfatminchild", ""
                        )

                        if father_mother == "1":
                            meta_data["proloc"] = meta_data.get("locat", "")
                            meta_data["prosizeofholdingarea"] = meta_data.get(
                                "size_of_holding", ""
                            )

                        elif father_mother == "2":
                            meta_data["loc"] = meta_data.get("locat", "")
                            meta_data["sizeofholdingarea"] = meta_data.get(
                                "size_of_holding", ""
                            )

                    if meta_data.get("Irrigated") == "1":
                        father_mother = meta_data["selectfathermotherforIrrigated"]

                        if father_mother == "1":
                            meta_data["proi"] = meta_data.get("I", "")
                            meta_data["proii"] = meta_data.get("II", "")
                            meta_data["proiii"] = meta_data.get("III", "")

                        elif father_mother == "2":
                            meta_data["i"] = meta_data.get("I", "")
                            meta_data["ii"] = meta_data.get("II", "")
                            meta_data["iii"] = meta_data.get("III", "")

                    if meta_data.get("unirrigated") == "1":
                        father_mother = meta_data.get("unirrigatedfathermotherboth", "")

                        if father_mother == "1":
                            meta_data["IVpercentageRightUnirrigated"] = meta_data.get(
                                "IV_Percentage_irrigated", ""
                            )
                            meta_data["VIflandholdingRightUnirrigated"] = meta_data.get(
                                "V_holding_irrigated", ""
                            )
                            meta_data["VIPercentageoftotalRightUnirrigated"] = (
                                meta_data.get("VI_Percentage_irrigated", "")
                            )

                        elif father_mother == "2":
                            meta_data["IVpercentageLeftUnirrigated"] = meta_data.get(
                                "IV_Percentage_irrigated", ""
                            )
                            meta_data["VIflandholdingLeftUnirrigated"] = meta_data.get(
                                "V_holding_irrigated", ""
                            )
                            meta_data["VIPercentageoftotalLeftUnirrigated"] = (
                                meta_data.get("VI_Percentage_irrigated", "")
                            )

                    if meta_data.get("plantation") == "1":
                        father_mother = meta_data.get("selectforplantation", "")

                        if father_mother == "1":
                            meta_data["procropsfruits"] = meta_data.get(
                                "crops_fruits", ""
                            )
                            meta_data["prolocation"] = meta_data.get("location_", "")
                            meta_data["proareaofplantation"] = meta_data.get(
                                "area_of_plantation", ""
                            )
                        elif father_mother == "2":
                            meta_data["cropsfruits"] = meta_data.get("crops_fruits", "")
                            meta_data["location"] = meta_data.get("location_", "")
                            meta_data["areaofplantation"] = meta_data.get(
                                "area_of_plantation", ""
                            )

                    if (
                        meta_data.get("vacantlandandbuildingsinurbanareasorurbanaggl")
                        == "1"
                    ):
                        father_mother = meta_data.get(
                            "selectforvacantlandandbuilinurbanareasorurbanaggl", ""
                        )

                        if father_mother == "1":
                            meta_data["prolocationofproperty"] = meta_data.get(
                                "Location_property", ""
                            )
                            meta_data["prodetailsofproperty"] = meta_data.get(
                                "Details_property", ""
                            )
                            meta_data["prousetowhichitisput"] = meta_data.get(
                                "Use_which_is_put", ""
                            )

                        elif father_mother == "2":
                            meta_data["locationofproperty"] = meta_data.get(
                                "Location_property", ""
                            )
                            meta_data["detailsofproperty"] = meta_data.get(
                                "Details_property", ""
                            )
                            meta_data["usetowhichitisput"] = meta_data.get(
                                "Use_which_is_put", ""
                            )

                    if meta_data.get("incomewealth") == "1":
                        father_mother = meta_data.get("selectforincomewealth", "")

                        if father_mother == "1":
                            meta_data["proannualfamincfromallsources"] = meta_data.get(
                                "annual_family_income", ""
                            )
                            meta_data["prowhethertaxprayer"] = meta_data.get(
                                "Whether_Tax_Prayer", ""
                            )
                            meta_data["prowhethercovinwealthtaxact"] = meta_data.get(
                                "Whether_covered_wealth_tax", ""
                            )
                            meta_data["prowealthtaxdet"] = meta_data.get(
                                "Wealth_Tax_Details", ""
                            )

                        elif father_mother == "2":
                            meta_data["annualfamincfromallsources"] = meta_data.get(
                                "annual_family_income", ""
                            )
                            meta_data["whethertaxprayer"] = meta_data.get(
                                "Whether_Tax_Prayer", ""
                            )
                            meta_data["whethercovinwealthtaxact"] = meta_data.get(
                                "Whether_covered_wealth_tax", ""
                            )
                            meta_data["wealthtaxdet"] = meta_data.get(
                                "Wealth_Tax_Details", ""
                            )
                    sebcCertAPI.getCaste()
                    check_data = {
                        "prossizeofholdingarea": {
                            "en": "size of holding area",
                            "od": "ଧରଣ ଅଞ୍ଚଳର ଆକାର",
                        },
                        "sizeofholdingarea": {
                            "en": "size of holding area",
                            "od": "ଧରଣ ଅଞ୍ଚଳର ଆକାର",
                        },
                        "proareaofplantation": {
                            "en": "area of plantation",
                            "od": "ପ୍ଲାଣ୍ଟେସନ୍ ଅଞ୍ଚଳ",
                        },
                        "areaofplantation": {
                            "en": "area of plantation",
                            "od": "ପ୍ଲାଣ୍ଟେସନ୍ ଅଞ୍ଚଳ",
                        },
                        "proannualfamincfromallsources": {
                            "en": "annual family income from all sources",
                            "od": "ସମସ୍ତ ସ୍ରୋତରୁ ବାର୍ଷିକ ପରିବାର ଆୟ",
                        },
                        "annualfamincfromallsources": {
                            "en": "annual family income from all sources",
                            "od": "ସମସ୍ତ ସ୍ରୋତରୁ ବାର୍ଷିକ ପରିବାର ଆୟ",
                        },
                    }
                    check = list(check_data.keys())
                    d = ""
                    f = ""
                    for c in check:
                        if c in meta_data:
                            if float(meta_data[c]) < 1:
                                d = "TEXT"
                                f = c
                                break
                            d = ""
                    if d == "TEXT":
                        log_message = f"{get_all_messages('MIN_VALUE_CHECK', 'EN').replace('~', check_data[f]['en'])}"
                        log_info = "USER_ERROR"
                        log_error = f"{get_all_messages('MIN_VALUE_CHECK', 'EN').replace('~', check_data[f]['en'])}"
                        response = {
                            "screen": "SCREEN_FOUR",
                            "data": {
                                "error": True,
                                "error_message": get_all_messages(
                                    "MIN_VALUE_CHECK", user_language
                                ).replace("~", check_data[f][user_language]),
                            },
                        }
                    else:
                        log_message = (
                            f"{SEBC_SCREEN_MAPPER.get(footer_type, '')} COMPLETED"
                        )
                        log_info = "INFO"
                        log_error = ""
                        response = {
                            "screen": "SCREEN_FIVE",
                            "data": {
                                "reqd": True,
                                "meta_data": meta_data,
                                "caste_visible": False,
                                "apply_to_office_init": [
                                    i["tehsil"]
                                    for i in sebc_tehsil
                                    if meta_data.get("presenttehasil", "")
                                    .split("_")[1]
                                    .lower()
                                    in i["tehsil"].lower()
                                ][0],
                            },
                        }

                elif footer_type == "SCREEN_FIVE":
                    meta_data = decrypted_data["data"]["meta_data"]

                    for key, value in decrypted_data["data"].items():
                        if key == "meta_data":
                            continue
                        meta_data[key] = value
                    log_message = f"{SEBC_SCREEN_MAPPER.get(footer_type, '')} COMPLETED"
                    log_info = "INFO"
                    log_error = ""
                    response = {
                        "screen": "SCREEN_SIX",
                        "data": {
                            "reqd": True,
                            "meta_data": meta_data,
                            "document_name_other_visible": False,
                            "upload_type": "Identity_Proof",
                            "button_activate": False,
                            "document_to_be_attached_visible": True,
                            "final_visible": False,
                            "upload_show": True,
                        },
                    }
                update.update(
                    {
                        "current": SEBC_SCREEN_MAPPER.get(footer_type, ""),
                        "meta_data": {
                            "msg": log_message,
                            "type": log_info,
                            "data": {},
                            "error": log_error,
                        },
                    }
                )

    except Exception:
        traceback.print_exc()
        # update.update({"current":SEBC_SCREEN_MAPPER.get(footer_type, ""), "meta_data":{"msg": log_message,"type":"FLOW_ERROR","data":{},"error": traceback.format_exc()}})
        response = {
            "screen": decrypted_data.get("screen", ""),
            "data": {"error": True, "error_message": "SOME ERROR OCCURED"},
        }
        update.update(
            {
                "current": SEBC_SCREEN_MAPPER.get(
                    decrypted_data["screen"], decrypted_data["screen"]
                ),
                "meta_data": {
                    "msg": "SOME ERROR OCCURED INSIDE THE FLOW",
                    "type": "FLOW_ERROR",
                    "data": {"payload": decrypted_data, "response": response},
                    "error": traceback.format_exc(),
                },
            }
        )

    if flowid:
        # db=OD_DB()
        flow_session = db.query(FlowLogs).filter(FlowLogs.flowmaster_id == flowid)
        flow_session.update(update)
        db.commit()
        # db.close()

    encrypted_response = encrypt_response(response, aes_key, iv)
    return PlainTextResponse(content=encrypted_response, media_type="text/plain")
