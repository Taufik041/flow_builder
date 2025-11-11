from fastapi import FastAPI, UploadFile, Query
from fastapi.responses import JSONResponse
from bot import extract_form_elements_from_image
from flow import ScreenBuilder
import json, os
from enum import Enum

class LanguageOptions(str, Enum):
    ENGLISH = "en-IN"
    HINDI = "hi-IN"
    ODIYA = "od-IN"

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/upload-image/")
async def upload_image(file: UploadFile, options: LanguageOptions = Query(LanguageOptions.ENGLISH)):
    API_KEY: str = os.getenv("OPENAI_API_KEY") or ""
    with open("temp_image.png", "wb") as buffer:
        buffer.write(await file.read())
    data = options
    language = data.replace("_", "-")
    result = json.loads(extract_form_elements_from_image("temp_image.png", API_KEY))
    for key, value in result.items():
        result[key]["translate"] = language
    screen_builder = ScreenBuilder(result)
    screen_json = screen_builder.build_flow()
    
    with open("output_flow.json", "w", encoding="utf-8") as f:
        f.write(screen_json)
    
    # return screen_json
    return JSONResponse(content=json.loads(screen_json))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
    