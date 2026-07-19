from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from config.database import get_db
import controllers.index_controller as controller
import schemas.index_schemas as schema

router = APIRouter(prefix="/index", tags=["index-analytics"])


@router.post("/{index_name}/upload", response_model=schema.UploadResponse)
async def upload_index_excel(
    index_name: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="File harus berformat .xlsx")

    file_bytes = await file.read()
    try:
        result = controller.ingest_excel_file(db, index_name, file.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return result


@router.post("/{index_name}/upload-batch")
async def upload_index_excel_batch(
    index_name: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    non_xlsx = [f.filename for f in files if not f.filename.endswith(".xlsx")]
    if non_xlsx:
        raise HTTPException(status_code=400, detail=f"File berikut bukan .xlsx: {non_xlsx}")

    file_payload = [(f.filename, await f.read()) for f in files]
    result = controller.ingest_multiple_files(db, index_name, file_payload)
    return result


@router.get("/{index_name}/periods", response_model=List[schema.PeriodOut])
def list_periods(index_name: str, db: Session = Depends(get_db)):
    return controller.get_periods(db, index_name)


@router.get("/{index_name}/analytics/simple-consistency", response_model=List[schema.ConsistencyOut])
def simple_consistency(index_name: str, db: Session = Depends(get_db)):
    results = controller.get_simple_consistency(db, index_name)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"Belum ada data untuk index '{index_name}'. Upload file dulu lewat /index/{index_name}/upload"
        )
    return results