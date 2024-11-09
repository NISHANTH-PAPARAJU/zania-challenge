from fastapi import FastAPI, File, UploadFile
from fastapi import HTTPException, status
from argparse import ArgumentParser
import uvicorn
import logging
from uuid import uuid4
import os
from helpers.slack_helper import post_to_slack
from agents.llama_index_agent import process_agent_request
from dotenv import load_dotenv
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
from agents.utils import clear_all_index_cache
from fastapi.middleware.cors import CORSMiddleware
from agents.custom_agent_workflow import process_custom_agent_request

class DocQARequest(BaseModel):
    file_location: str
    user_id: Optional[str] = "U0807FT9H6V"
    user_query: str

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
logger = logging.getLogger(__name__)


app.get("/ping")
async def ping():
    logger.info("Ping request.")
    resp = {}
    resp["responseCode"] = 200
    resp["responseDesc"] = "Alive!"


UPLOAD_DIR = Path("tmp")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist

@app.post("/uploadfile")
async def upload_file(file: UploadFile = File(...)):
    print(file.filename)
    file_location = UPLOAD_DIR / file.filename
    print(file_location)
    try:
        
        with open(file_location, "wb") as f:
            f.write(await file.read())
        clear_all_index_cache(folder_path="./tmp/cache/")
        return {"message": "File saved successfully", "file_path": str(file_location)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="File saving failed") from e


@app.post("/api/v1/doc-qa")
async def answer_doc_questions(request: DocQARequest):
    try:
        file_location = request.file_location
        user_query = request.user_query
        user_id = request.user_id #"U0807FT9H6V"
        request_id = str(uuid4())
        print(f"{user_query}, {user_id}, {request_id}, {file_location}")
        response = await process_custom_agent_request(
            request_id=request_id, 
            user_id = user_id,
            file=file_location, 
            user_query=user_query
        )
        # post_to_slack(message=str(response), user_id=user_id, request_id=request_id)
        return {"message": str(response), "request_id": request_id, "user_id":user_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occured while processing the request. Error:{e}"
        )
    

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-p", "--port", default=8000, type=int, help="port to listen on"
    )
    args = parser.parse_args()
    port = args.port
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)