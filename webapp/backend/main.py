from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Header
import os
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import declarative_base # Dùng cho SQLAlchemy mới
from datetime import datetime
from pydantic import BaseModel
import hashlib
import json
import time
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from eth_utils import keccak

try:
    from .inference import TomatoDiseaseSegmenter
except ImportError:
    from inference import TomatoDiseaseSegmenter

# --- DATABASE SETUP ---
# Khởi tạo kết nối SQLite bằng đường dẫn tuyệt đối để không phụ thuộc cwd hiện tại.
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Model dữ liệu (SQLAlchemy) làm tiền đề cho Blockchain
class Record(Base):
    __tablename__ = "records"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    infection_percentage = Column(Float)
    best_model = Column(String, index=True)
    best_model_label = Column(String)
    selection_basis = Column(String)
    record_timestamp = Column(String, index=True)
    record_sha256 = Column(String, index=True)
    record_keccak = Column(String, index=True)
    record_hash = Column(String, index=True) # Chuỗi băm đối chiếu (alias của record_keccak)
    record_payload_json = Column(Text)
    model_results_json = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Tự động tạo bảng khi khởi động app
Base.metadata.create_all(bind=engine)


def ensure_record_schema():
    inspector = inspect(engine)
    existing_columns = {column['name'] for column in inspector.get_columns('records')}
    required_columns = {
        'best_model': 'ALTER TABLE records ADD COLUMN best_model VARCHAR',
        'best_model_label': 'ALTER TABLE records ADD COLUMN best_model_label VARCHAR',
        'selection_basis': 'ALTER TABLE records ADD COLUMN selection_basis VARCHAR',
        'record_timestamp': 'ALTER TABLE records ADD COLUMN record_timestamp VARCHAR',
        'record_sha256': 'ALTER TABLE records ADD COLUMN record_sha256 VARCHAR',
        'record_keccak': 'ALTER TABLE records ADD COLUMN record_keccak VARCHAR',
        'model_results_json': 'ALTER TABLE records ADD COLUMN model_results_json TEXT',
        'record_payload_json': 'ALTER TABLE records ADD COLUMN record_payload_json TEXT',
    }

    with engine.begin() as connection:
        for column_name, ddl in required_columns.items():
            if column_name not in existing_columns:
                connection.execute(text(ddl))


ensure_record_schema()

# --- FASTAPI APP SETUP ---
app = FastAPI(title="AgriChain AI Backend")

# Cấu hình CORS Middleware: Cho phép Frontend truy cập mượt mà
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép tất cả nguồn chéo
    allow_credentials=True,
    allow_methods=["*"], # Cho phép GET, POST, OPTIONS...
    allow_headers=["*"],
)

# Khởi tạo bộ máy AI (Inference)
segmenter = TomatoDiseaseSegmenter()


def build_record_payload(
    filename: str,
    infection_percentage: float,
    best_model: str,
    best_model_label: str,
    selection_basis: str,
    model_results: list[dict] | None,
    record_timestamp: str,
) -> dict:
    return {
        "filename": filename,
        "infection_area_percent": infection_percentage,
        "best_model": best_model,
        "best_model_label": best_model_label,
        "selection_basis": selection_basis,
        "model_results": model_results or [],
        "timestamp": record_timestamp,
    }


# Dependency lấy Database Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- ADMIN / DEV: tamper endpoint (use only for local/dev demos)
@app.post("/admin/tamper")
async def admin_tamper(
    filename: str = Form(...),
    record_keccak: str = Form(...),
    record_sha256: str = Form(...),
    db: Session = Depends(get_db),
    x_admin_key: str | None = Header(None),
):
    """
    Dev-only endpoint to update the most recent `records` row for a filename.
    Protects with a simple `X-ADMIN-KEY` header. Default key: 'dev-key'.
    """
    admin_key = os.environ.get("ADMIN_KEY", "dev-key")
    if x_admin_key != admin_key:
        raise HTTPException(status_code=403, detail="Missing or invalid admin key")

    # Normalize values
    normalized_keccak = record_keccak if record_keccak.startswith("0x") else f"0x{record_keccak}"

    db_record = db.query(Record).filter(Record.filename == filename).order_by(Record.id.desc()).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")

    db_record.record_keccak = normalized_keccak
    db_record.record_sha256 = record_sha256
    db_record.record_hash = normalized_keccak
    db.commit()
    db.refresh(db_record)

    return {"status": "success", "id": db_record.id, "record_keccak": db_record.record_keccak}


def hash_record_payload(record_payload: dict) -> tuple[str, str, str]:
    payload_json = json.dumps(record_payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    payload_bytes = payload_json.encode("utf-8")
    record_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    record_keccak = "0x" + keccak(payload_bytes).hex()
    return payload_json, record_sha256, record_keccak

# --- ENDPOINTS ---

@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    model_type: str = Form("unet") # Mặc định là unet
):
    """
    API suy luận AI: Nhận ảnh tải lên và trả về kết quả dự đoán
    """
    start_time = time.time()
    
    # 1. Đọc bytes từ file tải lên
    image_bytes = await file.read()
    
    # 2. Chạy toàn bộ model và chọn kết quả tốt nhất để hiển thị
    results = segmenter.predict_all(image_bytes, preferred_model=model_type)
    
    # Tính thời gian inference ms
    inference_time_ms = int((time.time() - start_time) * 1000)
    record_timestamp = datetime.utcnow().isoformat()
    record_payload = build_record_payload(
        filename=file.filename,
        infection_percentage=results["infection_area_percent"],
        best_model=results["best_model"],
        best_model_label=results["best_model_label"],
        selection_basis=results["selection_basis"],
        model_results=results["model_results"],
        record_timestamp=record_timestamp,
    )
    record_payload_json, record_sha256, record_keccak = hash_record_payload(record_payload)
    
    return {
        "status": "success",
        "infection_area_percent": results["infection_area_percent"],
        "image_original_base64": results["image_original_base64"],
        "image_mask_base64": results["image_mask_base64"],
        "image_overlay_base64": results["image_overlay_base64"],
        "best_model": results["best_model"],
        "best_model_label": results["best_model_label"],
        "model_used": results["best_model"],
        "model_results": results["model_results"],
        "best_model_inference_time_ms": results["best_model_inference_time_ms"],
        "selection_basis": results["selection_basis"],
        "record_timestamp": record_timestamp,
        "record_payload": record_payload,
        "record_payload_json": record_payload_json,
        "record_sha256": record_sha256,
        "record_keccak": record_keccak,
        "record_hash": record_keccak,
        "inference_time_ms": inference_time_ms
    }

class VerifyRecordRequest(BaseModel):
    filename: str
    infection_percentage: float
    record_timestamp: str
    record_sha256: str | None = None
    record_keccak: str | None = None
    record_hash: str | None = None
    best_model: str | None = None
    best_model_label: str | None = None
    selection_basis: str | None = None
    model_results: list[dict] | None = None

@app.post("/verify_record")
async def verify_record(request: VerifyRecordRequest, db: Session = Depends(get_db)):
    """
    API lưu trữ đối chứng (Off-chain) cho Smart Contract
    """
    record_payload = build_record_payload(
        filename=request.filename,
        infection_percentage=request.infection_percentage,
        best_model=request.best_model or "",
        best_model_label=request.best_model_label or "",
        selection_basis=request.selection_basis or "",
        model_results=request.model_results,
        record_timestamp=request.record_timestamp,
    )
    record_payload_json, computed_sha256, computed_keccak = hash_record_payload(record_payload)
    provided_sha256 = request.record_sha256 or computed_sha256
    provided_keccak = request.record_keccak or request.record_hash or computed_keccak

    if request.record_sha256 and request.record_sha256.lower() != computed_sha256:
        raise HTTPException(status_code=400, detail="record_sha256 does not match canonical payload")

    normalized_keccak = provided_keccak if provided_keccak.startswith("0x") else f"0x{provided_keccak}"
    if request.record_keccak and normalized_keccak.lower() != computed_keccak.lower():
        raise HTTPException(status_code=400, detail="record_keccak does not match canonical payload")

    db_record = Record(
        filename=request.filename,
        infection_percentage=request.infection_percentage,
        record_timestamp=request.record_timestamp,
        record_sha256=provided_sha256,
        record_keccak=normalized_keccak,
        record_hash=normalized_keccak,
        record_payload_json=record_payload_json,
        best_model=request.best_model,
        best_model_label=request.best_model_label,
        selection_basis=request.selection_basis,
        model_results_json=(json.dumps(request.model_results, ensure_ascii=False) if request.model_results is not None else None)
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return {
        "status": "success", 
        "message": "Đã lưu bản ghi thành công", 
        "id": db_record.id
    }

@app.get("/record/{filename}")
async def get_record(filename: str, db: Session = Depends(get_db)):
    """
    API lấy dữ liệu từ DB nội bộ để kiểm tra chéo với Blockchain
    """
    # Lấy bản ghi mới nhất theo tên file
    record = db.query(Record).filter(Record.filename == filename).order_by(Record.id.desc()).first()
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy file này trong cơ sở dữ liệu (SQLite)")
        
    return {
        "filename": record.filename,
        "infection_percentage": record.infection_percentage,
        "best_model": record.best_model,
        "best_model_label": record.best_model_label,
        "selection_basis": record.selection_basis,
        "record_timestamp": record.record_timestamp,
        "record_sha256": record.record_sha256,
        "record_keccak": record.record_keccak,
        "record_hash": record.record_hash,
        "model_results": (json.loads(record.model_results_json) if record.model_results_json else None),
        "timestamp": record.timestamp.isoformat()
    }

# Mount frontend static files (serve SPA) after API routes so /predict is not shadowed.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
