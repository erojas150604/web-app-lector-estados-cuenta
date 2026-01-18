from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import pandas as pd

from app.db.session import get_db
from app.db.crud import get_job, update_job
from app.storage.local import read_json, job_dir
from app.storage.naming import build_excel_filename
from app.exporters.excel import df_to_excel

# Import parsers (para regenerar df completo en export)
from app.parsers.bbva_debito import BBVAParser
from app.parsers.bbva_tc import BBVATCParser

from app.formats.bbva_debito_raw import bbva_debito_to_raw
from app.formats.bbva_tc_raw import bbva_tc_to_raw


router = APIRouter()

def _parser_from_format_id(format_id: str):
    if format_id == "bbva_debito_v1":
        return BBVAParser()
    if format_id == "bbva_tc_v1":
        return BBVATCParser()
    return None

@router.get("/export/excel/{job_id}")
def export_excel(job_id: str, db: Session = Depends(get_db)):
    job = get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    if not job.input_pdf_path:
        raise HTTPException(status_code=400, detail="Job sin PDF asociado")

    parser = _parser_from_format_id(job.formato_id)
    if not parser:
        raise HTTPException(status_code=400, detail=f"No hay parser conectado para formato: {job.formato_id}")

    # Re-parse para obtener DF completo (MVP).
    # Más adelante: cachear df en parquet o guardar movimientos.
    df = parser.parse_movimientos(job.input_pdf_path)
    if df is None or df.empty:
        raise HTTPException(status_code=422, detail="No se encontraron movimientos al exportar")

    # 🔽 CONVERSIÓN A RAW (solo para export)
    if job.formato_id == "bbva_debito_v1":
        df_excel = bbva_debito_to_raw(df)
        currency_cols = [
            "CARGOS",
            "ABONOS",
            "SALDO OPERACIÓN",
            "SALDO LIQUIDACIÓN",
        ]

    elif job.formato_id == "bbva_tc_v1":
        df_excel = bbva_tc_to_raw(df)
        currency_cols = [
            "IMPORTE CARGOS",
            "IMPORTE ABONOS",
        ]

    else:
        df_excel = df  # fallback por ahora

    out_dir = job_dir(job_id)
    out_path = out_dir / "output.xlsx"
    df_to_excel(df_excel, out_path, currency_columns=currency_cols)



    job.excel_path = str(out_path)
    job.status = "exported"
    update_job(db, job)

    filename = build_excel_filename(job.banco, job.tipo_producto, job.date_from, job.date_to)
    return FileResponse(
        path=str(out_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
