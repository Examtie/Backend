from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query
from typing import List, Dict, Any
from datetime import datetime
from bson import ObjectId

from app.models import Flashcard, FlashcardRecordOut, ExamQuestion, ExamRecordOut
from app.dependencies import get_current_user
from app.database import flashcards_collection, ai_exam_questions_collection
from app.settings import TPYTHON_API_KEY, Azure_API_KEY


from ai_runner.Typhoon import Typhoon_API
from ai_runner.PDFExtrack import CLIENT_OCR
from ai_runner.AAzure import Azzzure_API

router = APIRouter(
    prefix="/ai/api/v1",
    tags=["ai"],
)

#api_typhoon = Typhoon_API(api_key=TPYTHON_API_KEY)
Client_OCR = CLIENT_OCR()
api_azure = Azzzure_API(api_key=Azure_API_KEY)

def extract_flashcards(doc):
    fc = doc.get("flashcards")
    if isinstance(fc, dict) and "flashcards" in fc:
        return fc["flashcards"]
    elif isinstance(fc, list):
        return fc
    else:
        return []

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

    #data = api_typhoon.generate_flashcards(topic=context, amount=amount)
    data = api_azure.generate_flashcards(context=context, amount=amount)
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
        context = Client_OCR.ocr(pdf_bytes=pdf_bytes)
    else:
        context = prompt
    if not context:
        raise HTTPException(status_code=400, detail="No context available for exam generation")

    #questions = api_typhoon.generate_exam_questions(context=context, amount=amount)
    questions = api_azure.generate_exam_questions(context=context, amount=amount)
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
        filename_or_prompt = doc.get("filename", "")
        if not filename_or_prompt:
            filename_or_prompt = doc.get("prompt", "")
            
        records.append(
            FlashcardRecordOut(
                id=str(doc["_id"]),
                filename_or_prompt=filename_or_prompt,
                created_at=doc["created_at"],
                flashcards=[Flashcard(**fc) for fc in extract_flashcards(doc)],
            )
        )
    return records



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
    
    # Ensure that exam_data is iterable (i.e. a list)
    if not isinstance(exam_data, list):
        raise HTTPException(
            status_code=500,
            detail="Exam question generation failed: Unexpected response format."
        )

    record = {
        "user_id": str(current_user.get("_id") or current_user.get("id")),
        "prompt": prompt,
        "created_at": datetime.utcnow(),
        "exam": exam_data,
    }
    await ai_exam_questions_collection.insert_one(record)

    return [
        ExamQuestion(
            id=str(i + 1),
            type="multiple_choice",
            question=q.get("question"),
            choices=q.get("options"),
            answer=q.get("correct_answer")
        )
        for i, q in enumerate(exam_data)
    ]


@router.get("/exam/history", response_model=List[ExamRecordOut])
async def list_exam_history(
    limit: int = Query(20, ge=1, le=100, description="Number of history records to return"),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user.get("_id") or current_user.get("id"))
    records: List[ExamRecordOut] = []
    cursor = (
        ai_exam_questions_collection.find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    async for doc in cursor:
        file_or_prompt = doc.get("filename", "") or doc.get("prompt", "")
        questions = doc.get("exam", [])
        # If questions isn't a list, set it to an empty list.
        if not isinstance(questions, list):
            questions = []
        exam_qs = []
        for index, q in enumerate(questions):
            exam_qs.append(
                ExamQuestion(
                    id=str(index + 1),
                    type="multiple_choice",
                    question=q.get("question"),
                    choices=q.get("options"),
                    answer=q.get("correct_answer")
                )
            )
        records.append(
            ExamRecordOut(
                id=str(doc.get("_id") or doc.get("id") or "0"),
                filename_or_prompt=file_or_prompt,
                created_at=doc.get("created_at"),
                exam_questions=exam_qs
            )
        )
    return records