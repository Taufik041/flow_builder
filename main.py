from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
from bot_prompt import process_image_and_prompt
from screen import ScreenBuilder
from components import ComponentBuilder
import json, os
from typing import Optional
from json_modifications import modify_json

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/upload-image/")
async def upload_image(file: Optional[UploadFile] = None, prompt: Optional[str] = None):
    API_KEY: str = os.getenv("OPENAI_API_KEY") or ""
    if file is None:
        image = None
    else:
        with open("temp_image.png", "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    try:
        result = json.loads(process_image_and_prompt("temp_image.png" if file is not None else None, prompt, API_KEY))
        result = json.loads(modify_json(result))
        
        if result["type"].lower() == "screen":
            builder = ScreenBuilder(result["image"], result["screen_name"] if "screen_name" in result else "Default Screen")
            screen_json = builder.build_screen()
            return JSONResponse(content=json.loads(screen_json))
        
        elif result["type"].lower() == "components":
            builder = ComponentBuilder(result["image"])
            data_json, layout_children = builder.build_component()
            final_result = {
                "data": json.loads(data_json),
                "children": json.loads(layout_children)
            }
            return JSONResponse(content=final_result)
        
    except Exception as e:
        import traceback; traceback.print_exc();
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
    