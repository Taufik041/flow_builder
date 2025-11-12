import json
import uuid
import re


def generate_short_uuid():
    """Generate a short UUID"""
    return str(uuid.uuid4()).replace('-', '')[:8]

def process_image(image_obj, add, remove):
    """Process the image object by removing and adding fields"""
    result = image_obj.copy()
    
    # Step 1: Remove fields where the name matches values in remove_obj
    for remove_obj in remove:
        values_to_remove = [v.lower() for v in remove_obj.values()]
        keys_to_delete = []
        
        for key, value in result.items():
            if isinstance(value, dict) and 'name' in value:
                if value['name'].lower() in values_to_remove:
                    keys_to_delete.append(key)
                    print(f'Removed: {key} with name "{value["name"]}"')
        
        for key in keys_to_delete:
            del result[key]
        
    # Step 2: Add new fields from add_obj
    for add_obj in add:
        for original_key, name_value in add_obj.items():
            if original_key == 'required':  # Skip the required flag
                continue
            
            # Extract the base type (e.g., "dropdown" from "dropdown1")
            base_type = re.sub(r'\d+', '', original_key)
            # Generate a unique key with UUID
            unique_key = f"{base_type}{generate_short_uuid()}"
            
            # Add the new field
            result[unique_key] = {
                "name": name_value.capitalize(),
                "required": add_obj.get('required', False),
                "translate": "od-IN"
            }
            
            print(f'Added: {unique_key} with name "{name_value.capitalize()}"')
        
    return result

def modify_json(data):
    """Modify the JSON data by processing the image section"""
    LANG_MAP = {
        "english": "en-IN",
        "hindi": "hi-IN",
        "odia": "od-IN",
        "bengali": "bn-IN"
    }
    image = data.get('image', {})
    add = data.get('add', [])
    remove = data.get('remove', [])
    
    modified_image = process_image(image, add, remove)    
    for key, value in modified_image.items():
        modified_image[key]['translate'] = LANG_MAP[data['language'].lower()]

    final_result = {**data, 'image': modified_image}

    return json.dumps(final_result)

if __name__ == "__main__":
    # Original data
    data = {
        "image": {
            "dropdown1": {
                "name": "Select Type Of Organization",
                "required": True,
                "translate": "od-IN"
            },
            "textinput1": {
                "name": "Applicant Name",
                "required": True,
                "translate": "od-IN"
            },
            "textinput2": {
                "name": "Mobile Number",
                "required": True,
                "translate": "od-IN"
            },
            "textinput3": {
                "name": "E-Mail",
                "required": True,
                "translate": "od-IN"
            },
            "dropdown2": {
                "name": "Whether Honble Governor/Chief Minister is invited as Chief Guest",
                "required": True,
                "translate": "od-IN"
            }
        },
        "add": [
            {"dropdown1": "state","required": False},
            {"dropdown1": "Gender","required": False}
        ],
        "remove": [
            {"textinput1": "applicant Name"},
            {"textinput1": "Mobile Number"},
        ],
        "type": "screen",
        "language": "EngLIsh"
    }

    print(modify_json(data))