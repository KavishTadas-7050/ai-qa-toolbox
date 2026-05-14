from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from auditor import analyze, capture, DEFAULT_URL


app = FastAPI(title="AI UI Auditor", version="1.0.0")


class AuditURLRequest(BaseModel):
    url: str = DEFAULT_URL


@app.post("/audit/url")
async def audit_url(request: AuditURLRequest):
    try:
        image_bytes = capture(request.url)
        issues = analyze(image_bytes)
        return JSONResponse(
            content={"url": request.url, "issue_count": len(issues), "issues": issues}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/audit/upload")
async def audit_upload(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        issues = analyze(image_bytes)
        return JSONResponse(
            content={
                "filename": file.filename,
                "issue_count": len(issues),
                "issues": issues,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
