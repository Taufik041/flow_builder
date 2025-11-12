import base64
import json
import requests
from typing import Dict, Optional
import os
import re

def extract_form_elements_from_image(
    image_path: str,
    api_key: str,
    model: str = "gpt-4o"
):
    """
    Extract form elements from a UI screenshot using OpenAI API.
    
    Args:
        image_path: Path to the image file
        api_key: OpenAI API key
        model: OpenAI model to use (default: gpt-4o)
    
    Returns:
        JSON string with extracted form elements
    """
    
    # Read and encode image
    try:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise Exception(f"Failed to read image: {str(e)}")
    
    # Prepare API request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "max_tokens": 2000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        Analyze this form/UI image and extract all form elements. For each element, identify:
                        1. The type (textinput, textheading, dropdown, textarea, checkboxgroup, radiobuttonsgroup, optin etc.)
                        2. The label or placeholder text

                        Return ONLY a valid JSON object with keys like "textinput1", "dropdown1", "textbody1", "radiobuttonsgroup1", "checkboxgroup1" etc., and values as the label text.

                        Example output format:
                        {"textinput1": {"name": "Mobile Number", "required": true}, "textinput2": {"name": "PAN", "required": false}, "dropdown1": {"name": "Gender", "required": true}, "dropdown2": {"name": "District", "required": true}, "textinput3": {"name": "Pincode", "required": false}
                        "checkboxgroup1":{"name":"Subscribe to newsletter","required":false,"options":["Yes","No"]}, "optin1":{"name":"Accept Terms","required":true}, "radiobuttonsgroup1":{"name":"Choose Option","required":true,"options":["Option 1","Option 2"]}}

                        Do not include any markdown formatting, backticks, or explanatory text. Return only the raw JSON object.
                        """
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }
    
    # Make API call
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")
    
    # Parse response
    try:
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Clean up response (remove markdown code blocks if present)
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON
        form_data = json.loads(content)
        return json.dumps(form_data)
        
    except (KeyError, json.JSONDecodeError) as e:
        raise Exception(f"Failed to parse API response: {str(e)}")


def parse_user_prompt(
    prompt: str,
    api_key: str,
    model: str = "gpt-4o"
):
    """
    Parse user prompt to extract language, type, add, and remove instructions.
    
    Args:
        prompt: User's text prompt
        api_key: OpenAI API key
        model: OpenAI model to use (default: gpt-4o)
    
    Returns:
        JSON string with parsed instructions
        Example: {"language": "English", "type": "screen", "add": {}, "remove": {}}
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": f"""Analyze this user prompt and extract the following information:

                1. Language: What language does the user want (English, Odia, Hindi, etc.)? Default is "English" if not specified.
                2. Type: Is it "screen" or "components"? Default is "components" if not specified. If its screen then a screen_name is also expected.
                3. Add: What form elements should be added? and are they required(default is False)? Format as {{"dropdown1": "Gender", "required": true}} and {{"textinput1": "Email", "required": true}}, etc. as a list
                4. Remove: What form elements should be removed? Format as {{"dropdown1": "Gender"}} and {{"textinput2": "PAN"}}, etc. as a list

                User prompt: "{prompt}"

                Return ONLY a valid JSON object in this exact format:
                {{"language": "English", "type": "screen", "add": {{}}, "remove": {{}}, "screen_name": {{}}}}

                If add or remove have items, include them. If they're empty, use empty objects {{}}.
                Do not include any markdown formatting, backticks, or explanatory text. Return only the raw JSON object.
                """
            }
        ]
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")
    
    try:
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Clean up response
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON
        parsed_data = json.loads(content)
        return json.dumps(parsed_data)
        
    except (KeyError, json.JSONDecodeError) as e:
        raise Exception(f"Failed to parse API response: {str(e)}")


def process_image_and_prompt(
    image_path: Optional[str],
    prompt: Optional[str],
    api_key: str,
    model: str = "gpt-4o"
):
    """
    Process both image and prompt, returning combined results.
    
    Args:
        image_path: Path to the image file (optional)
        prompt: User's text prompt (optional)
        api_key: OpenAI API key
        model: OpenAI model to use (default: gpt-4o)
    
    Returns:
        JSON string with format:
        {
            "image": {...},
            "add": {...},
            "remove": {...},
            "type": "screen",
            "language": "English",
            "screen_name": "Screen"
        }
    """
    
    result = {
        "image": {},
        "add": {},
        "remove": {},
        "type": "screen",
        "language": "English",
        "screen_name": ""
    }
    
    # Process image if provided
    if image_path:
        try:
            image_json = extract_form_elements_from_image(image_path, api_key, model)
            result["image"] = json.loads(image_json)
        except Exception as e:
            print(f"Error processing image: {e}")
    
    # Process prompt if provided
    if prompt:
        try:
            prompt_json = parse_user_prompt(prompt, api_key, model)
            prompt_data = json.loads(prompt_json)
            
            result["language"] = prompt_data.get("language", "English")
            result["type"] = prompt_data.get("type", "screen")
            result["add"] = prompt_data.get("add", {})
            result["remove"] = prompt_data.get("remove", {})
            result["screen_name"] = prompt_data.get("screen_name", "Screen")
        except Exception as e:
            print(f"Error processing prompt: {e}")
    
    return json.dumps(result, indent=2)


# Example usage
if __name__ == "__main__":
    API_KEY: str = os.getenv("OPENAI_API_KEY") or ""
    
    result2 = process_image_and_prompt(
        image_path="D:\\flowai\\flow_builder\\temp_image.png",
        prompt="Remove the dropdown gender and textinput mobile number and applicant name and add a dropdown for State. Make it in Odia language. This is for components.",
        api_key=API_KEY
    )
    print("\n" + "="*50 + "\n")
    print(result2)
    print("\n" + "="*50 + "\n")