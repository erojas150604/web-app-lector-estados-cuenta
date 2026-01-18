from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid
import pandas as pd

from app.db.session import get_db
from app.db.models import Job
from app.db.crud import create_job, update_job

from app.storage.local import save_bytes, save_json
from app.core.detector import detect_format
from app.core.schemas import ParseResponse, ParseMeta, Movement

# Import parsers
from app.parsers.bbva_debito import BBVAParser
from app.parsers.bbva_tc import BBVATCParser

from app.utils.json_sanitize import sanitize_records


router = APIRouter()

def _parser_from_format_id(format_id: str):
    # Mapeo simple (luego se hace dinámico)
    if format_id == "bbva_debito_v1":
        return BBVAParser()
    if format_id == "bbva_tc_v1":
        return BBVATCParser()
    return None

@router.post("/parse", response_model=ParseResponse)
async def parse_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())

    # Guardar PDF
    pdf_bytes = await file.read()
    safe_name = (file.filename or "input.pdf").replace("/", "_").replace("\\", "_")
    input_path = save_bytes(job_id, safe_name, pdf_bytes)


    # Crear job inicial
    job = Job(
        id=job_id,
        status="uploaded",
        input_pdf_path=str(input_path),
        banco="UNKNOWN",
        formato_id="UNKNOWN",
        tipo_producto="UNKNOWN",
    )
    job = create_job(db, job)

    try:
        fmt, _text = detect_format(str(input_path))
        job.banco = fmt.banco
        job.formato_id = fmt.id
        job.tipo_producto = fmt.tipo_producto
        job.status = "detected"
        job = update_job(db, job)

        parser = _parser_from_format_id(fmt.id)
        if not parser:
            raise HTTPException(status_code=400, detail=f"No hay parser conectado para formato: {fmt.id}")

        df = parser.parse_movimientos(str(input_path))
        if df is None or df.empty:
            job.status = "failed"
            job.error = "No se encontraron movimientos"
            update_job(db, job)
            raise HTTPException(status_code=422, detail="No se encontraron movimientos en el PDF.")

        # Conteo + rango de fechas (mejorable)
        job.movimientos_count = int(len(df))
        # intenta estimar rango con fecha_liquidacion o fecha_operacion
        date_col = "fecha_liquidacion" if "fecha_liquidacion" in df.columns else "fecha_operacion"
        if date_col in df.columns:
            dts = pd.to_datetime(df[date_col], errors="coerce")
            if dts.notna().any():
                job.date_from = dts.min().strftime("%Y-%m-%d")
                job.date_to = dts.max().strftime("%Y-%m-%d")

        if "cuenta" in df.columns and df["cuenta"].notna().any():
            job.cuenta = str(df["cuenta"].dropna().iloc[0])

        if "moneda" in df.columns and df["moneda"].notna().any():
            job.moneda = str(df["moneda"].dropna().iloc[0])
    
        # Guardar preview JSON (primeras 50 filas)
        preview_df = df.head(50).copy()

        # records crudos
        preview_records = preview_df.to_dict(orient="records")

        # ✅ limpiar NaN/Inf/fechas para JSON
        preview_records = sanitize_records(preview_records)

        preview_path = save_json(job_id, "preview.json", {"rows": preview_records})
        job.preview_json_path = str(preview_path)
        job.status = "parsed"
        update_job(db, job)

        preview_models = [Movement(**r) for r in preview_records]

        meta = ParseMeta(
            banco=job.banco,
            formato_id=job.formato_id,
            tipo_producto=job.tipo_producto,
            movimientos_count=job.movimientos_count,
            date_from=job.date_from,
            date_to=job.date_to,
        )
        return ParseResponse(job_id=job_id, meta=meta, preview=preview_models)

    except HTTPException:
        raise
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        update_job(db, job)
        raise HTTPException(status_code=500, detail=f"Error al procesar: {e}")
