from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from app.db.base import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)  # uuid str

    banco = Column(String, nullable=False, default="UNKNOWN")
    formato_id = Column(String, nullable=False, default="UNKNOWN")  # ej: bbva_debito_v1
    tipo_producto = Column(String, nullable=False, default="UNKNOWN")  # DEBITO / TC
    moneda = Column(String, nullable=True)
    cuenta = Column(String, nullable=True)

    status = Column(String, nullable=False, default="uploaded")  # uploaded/parsed/exported/failed
    error = Column(Text, nullable=True)

    movimientos_count = Column(Integer, nullable=False, default=0)
    date_from = Column(String, nullable=True)  # ISO string
    date_to = Column(String, nullable=True)

    input_pdf_path = Column(Text, nullable=True)
    preview_json_path = Column(Text, nullable=True)
    excel_path = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
