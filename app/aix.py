from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query
from typing import List, Dict, Any
from datetime import datetime
from bson import ObjectId

from app.models import Flashcard, FlashcardRecordOut, ExamQuestion
from app.dependencies import get_current_user
from app.database import flashcards_collection, ai_exam_questions_collection
from app.settings import TPYTHON_API_KEY


from ai_runner.Typhoon import Typhoon_API
from ai_runner.PDFExtrack import CLIENT_OCR

router = APIRouter(
    prefix="/ai/api/v1",
    tags=["ai"],
)

api_typhoon = Typhoon_API(api_key=TPYTHON_API_KEY)
Client_OCR = CLIENT_OCR()

# -----------------------------------------------------
# Helper – placeholder OCR & LLM processing
# -----------------------------------------------------
async def _generate_flashcard(pdf_bytes: bytes = None, prompt: str = None, amount: int = 10):
    if not pdf_bytes and not prompt:
        raise HTTPException(status_code=400, detail="Either PDF bytes or prompt must be provided")
    if pdf_bytes:
        print("Processing PDF bytes...")
        #print(pdf_bytes)
        context = Client_OCR.ocr(pdf_bytes=pdf_bytes)
    else:
        context = prompt
    if not context:
        raise HTTPException(status_code=400, detail="No context available for flashcard generation")
    print(f"Generating {amount} flashcards for context: {context}")

    data = api_typhoon.generate_flashcards(topic=context, amount=amount)
    print(data)

    return data

# -----------------------------------------------------
# Helper – generate exam questions
# -----------------------------------------------------
async def _generate_exam(pdf_bytes: bytes = None, prompt: str = None, amount: int = 10):
    if not pdf_bytes and not prompt:
        raise HTTPException(status_code=400, detail="Either PDF bytes or prompt must be provided")
    if pdf_bytes:
        print("Processing PDF bytes for exam generation...")
        context = Client_OCR.ocr(pdf_bytes)
    else:
        context = prompt
    if not context:
        raise HTTPException(status_code=400, detail="No context available for exam generation")

    questions = api_typhoon.generate_exam_questions(context=context, amount=amount)
    return questions

# -----------------------------------------------------
# Routes
# -----------------------------------------------------

@router.post("/flashcards/generate-pdf", response_model=List[Flashcard])
async def generate_flashcards(
    file: UploadFile = File(None, description="Optional PDF file to convert into flashcards"),
    amount: int = Query(10, ge=1, le=100, description="Number of flashcards to generate"),
    current_user: dict = Depends(get_current_user),
):
    """Upload a PDF, run OCR & LLM pipeline, and return generated flashcards."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a PDF")

    pdf_bytes = await file.read()

    # Placeholder processing – user to implement
    flashcards_data = await _generate_flashcard(pdf_bytes=pdf_bytes, amount=amount)

    # Store history record
    record = {
        "user_id": str(current_user.get("_id") or current_user.get("id")),
        "filename": file.filename,
        "created_at": datetime.utcnow(),
        "flashcards": flashcards_data,
    }
    result = await flashcards_collection.insert_one(record)

    return flashcards_data['flashcards']

@router.post("/flashcards/generate-text", response_model=List[Flashcard])
async def generate_flashcards(
    amount: int = Query(10, ge=1, le=100, description="Number of flashcards to generate"),
    prompt: str = Query(None, description="Optional prompt to guide flashcard generation"),
    current_user: dict = Depends(get_current_user),
):

    flashcards_data = await _generate_flashcard(prompt=prompt, amount=amount)
    
    record = {
        "user_id": str(current_user.get("_id") or current_user.get("id")),
        "prompt": prompt,
        "created_at": datetime.utcnow(),
        "flashcards": flashcards_data,
    }
    result = await flashcards_collection.insert_one(record)

    return flashcards_data['flashcards']


# -----------------------------------------------------
# Exam Generation Routes
# -----------------------------------------------------

@router.post("/exam/generate-pdf", response_model=List[ExamQuestion])
async def generate_exam_questions_pdf(
    file: UploadFile = File(None, description="Optional PDF file to convert into exam questions"),
    amount: int = Query(5, ge=1, le=100, description="Number of exam questions to generate"),
    current_user: dict = Depends(get_current_user),
):
    """Upload a PDF, run OCR & LLM pipeline, and return generated exam questions."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a PDF")

    pdf_bytes = await file.read()

    exam_data = await _generate_exam(pdf_bytes=pdf_bytes, amount=amount)

    record = {
        "user_id": str(current_user.get("_id") or current_user.get("id")),
        "filename": file.filename,
        "created_at": datetime.utcnow(),
        "exam": exam_data,
    }
    await ai_exam_questions_collection.insert_one(record)

    return [ExamQuestion(id=str(i + 1), type="multiple_choice", question=q.get("question"), choices=q.get("options"), answer=q.get("correct_answer")) for i, q in enumerate(exam_data)]


@router.post("/exam/generate-text", response_model=List[ExamQuestion])
async def generate_exam_questions_text(
    amount: int = Query(5, ge=1, le=100, description="Number of exam questions to generate"),
    prompt: str = Query(None, description="Optional prompt to guide exam question generation"),
    current_user: dict = Depends(get_current_user),
):
    """Generate exam questions based on a text prompt."""
    exam_data = await _generate_exam(prompt=prompt, amount=amount)

    record = {
        "user_id": str(current_user.get("_id") or current_user.get("id")),
        "prompt": prompt,
        "created_at": datetime.utcnow(),
        "exam": exam_data,
    }
    await ai_exam_questions_collection.insert_one(record)

    return [ExamQuestion(id=str(i + 1), type="multiple_choice", question=q.get("question"), choices=q.get("options"), answer=q.get("correct_answer")) for i, q in enumerate(exam_data)]


@router.get("/flashcards/history", response_model=List[FlashcardRecordOut])
async def list_flashcard_history(
    limit: int = Query(20, ge=1, le=100, description="Number of history records to return"),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user.get("_id") or current_user.get("id"))
    records: List[FlashcardRecordOut] = []
    cursor = (
        flashcards_collection.find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    async for doc in cursor:
        records.append(
            FlashcardRecordOut(
                id=str(doc["_id"]),
                user_id=doc["user_id"],
                filename=doc["filename"],
                created_at=doc["created_at"],
                flashcards=[Flashcard(**fc) for fc in doc["flashcards"]],
            )
        )
    return records


@router.get("/exam/{record_id}", response_model=FlashcardRecordOut)
async def get_flashcard_record(record_id: str, current_user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(record_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid record ID format")

    doc = await flashcards_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Record not found")

    user_id = str(current_user.get("_id") or current_user.get("id"))
    if doc.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this record")

    return FlashcardRecordOut(
        id=str(doc["_id"]),
        user_id=doc["user_id"],
        filename=doc["filename"],
        created_at=doc["created_at"],
        flashcards=[Flashcard(**fc) for fc in doc["flashcards"]],
    )

