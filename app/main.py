from pathlib import Path
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload
from .database import Base, SessionLocal, engine, get_db
from .models import CertificateRecord, GenerationJob
from .schemas import JobAccepted, JobCreate, JobResult, RecipientResult
from .certificates import generate_certificate

Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Bulk Certificate Generator API",
    description="Submit bulk certificate jobs, track results, and download generated PDF certificates.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent.parent / "static"), name="static")

def process_job(job_id: int) -> None:
    """Background worker. Each recipient is handled independently."""
    db = SessionLocal()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return
        job.status = "processing"
        db.commit()

        records = db.query(CertificateRecord).filter(CertificateRecord.job_id == job_id).all()
        for record in records:
            try:
                path = generate_certificate(record.recipient_name, job.event_name, record.id)
                record.file_path = path
                record.status = "success"
                record.error_message = None
            except Exception as exc:
                # One failed PDF must not prevent remaining recipients from processing.
                record.status = "failed"
                record.error_message = str(exc)[:1000]
            db.commit()

        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        job.success_count = db.query(CertificateRecord).filter_by(job_id=job_id, status="success").count()
        job.failure_count = db.query(CertificateRecord).filter_by(job_id=job_id, status="failed").count()
        if job.failure_count == 0:
            job.status = "completed"
        elif job.success_count == 0:
            job.status = "failed"
        else:
            job.status = "completed_with_errors"
        db.commit()
    finally:
        db.close()

@app.get("/", include_in_schema=False)
def root():
    return FileResponse(Path(__file__).resolve().parent.parent / "static" / "index.html")

@app.post("/jobs", response_model=JobAccepted, status_code=202)
def create_job(payload: JobCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = GenerationJob(
        event_name=payload.event_name.strip(),
        status="queued",
        total_count=len(payload.recipients),
        success_count=0,
        failure_count=0,
    )
    db.add(job)
    db.flush()
    for recipient in payload.recipients:
        db.add(CertificateRecord(
            job_id=job.id,
            recipient_name=recipient.name.strip(),
            recipient_email=str(recipient.email),
            status="pending",
        ))
    db.commit()
    db.refresh(job)
    background_tasks.add_task(process_job, job.id)
    return JobAccepted(job_id=job.id, status=job.status, message="Generation job accepted.")

@app.get("/jobs/{job_id}", response_model=JobResult)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = (
        db.query(GenerationJob)
        .options(joinedload(GenerationJob.certificates))
        .filter(GenerationJob.id == job_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    recipients = []
    for cert in job.certificates:
        recipients.append(RecipientResult(
            id=cert.id,
            name=cert.recipient_name,
            email=cert.recipient_email,
            status=cert.status,
            error_message=cert.error_message,
            download_url=f"/certificates/{cert.id}/download" if cert.status == "success" else None,
        ))
    return JobResult(
        id=job.id,
        event_name=job.event_name,
        status=job.status,
        total_count=job.total_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
        recipients=recipients,
    )

@app.get("/jobs/{job_id}/certificates")
def list_job_certificates(job_id: int, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    records = db.query(CertificateRecord).filter(CertificateRecord.job_id == job_id).all()
    return {
        "job_id": job_id,
        "certificates": [
            {
                "id": r.id,
                "name": r.recipient_name,
                "email": r.recipient_email,
                "status": r.status,
                "error_message": r.error_message,
                "download_url": f"/certificates/{r.id}/download" if r.status == "success" else None,
            } for r in records
        ],
    }

@app.get("/certificates/{certificate_id}/download")
def download_certificate(certificate_id: int, db: Session = Depends(get_db)):
    record = db.query(CertificateRecord).filter(CertificateRecord.id == certificate_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if record.status != "success" or not record.file_path:
        raise HTTPException(status_code=409, detail="Certificate is not available for download")
    path = Path(record.file_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Certificate file is missing")
    return FileResponse(path, media_type="application/pdf", filename=path.name)
