from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from modules.load_vectorstore import load_vectorstore
from logger import logger


router=APIRouter()

@router.post("/upload_pdfs/")
async def upload_pdfs(
    files: list[UploadFile] = File(
        ...,
        description="Upload one or more PDF files.",
    )
):
    try:
        logger.info("Received uploaded files")

        valid_files = []
        for file in files:
            if not file.filename:
                continue
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(
                    status_code=400,
                    detail=f"{file.filename} is not a PDF file.",
                )
            valid_files.append(file)

        if not valid_files:
            raise HTTPException(status_code=400, detail="Please upload at least one PDF file.")

        processed_files = load_vectorstore(valid_files)
        logger.info("Document added to vectorstore")
        return {
            "message": "Files processed and vectorstore updated",
            "files": processed_files,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during PDF upload")
        return JSONResponse(status_code=500,content={"error":str(e)})
