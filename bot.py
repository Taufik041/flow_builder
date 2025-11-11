import base64
import json
import requests
from typing import Dict, Optional
import os

def extract_form_elements_from_image(
    image_path: str,
    api_key: str,
    model: str = "gpt-4o"
):
    
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
                        1. The type (textinput, textarea, dropdown, checkboxgroup, radiobuttonsgroup, etc.)
                        2. The label or placeholder text

                        Return ONLY a valid JSON object with keys like "textinput1", "dropdown1", etc., and values as the label text.

                        Example output format:
                        {"textinput1": {"name": "Mobile Number", "required": true}, "textinput2": {"name": "PAN", "required": false}, "dropdown1": {"name": "Gender", "required": true}, "dropdown2": {"name": "District", "required": true}, "textinput3": {"name": "Pincode", "required": false}}

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


# Example usage
if __name__ == "__main__":
    API_KEY: str = os.getenv("OPENAI_API_KEY") or ""
    image_path = "D:\\flow-builder\\image.png"
    
    try:
        result = extract_form_elements_from_image(image_path, API_KEY)
        print(result)
    except Exception as e:
        print(f"Error: {e}")