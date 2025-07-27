from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query
from typing import List, Dict, Any
from datetime import datetime
from bson import ObjectId

from app.models import Flashcard, FlashcardRecordOut, ExamQuestion, ExamRecordOut, Ai_ExamSubmission, Ai_ExamResult, AiSubmissionRecordOut
from app.dependencies import get_current_user
from app.database import flashcards_collection, ai_exam_questions_collection, ai_exam_submissions_collection
from app.settings import TPYTHON_API_KEY, Azure_API_KEY, Azure_Endpoint, Azure_API_Version, Azure_Model


from ai_runner.Typhoon import Typhoon_API
from ai_runner.PDFExtrack import CLIENT_OCR
from ai_runner.AAzure import Azzzure_API

router = APIRouter(
    prefix="/ai/api/v1",
    tags=["ai"],
)

#api_typhoon = Typhoon_API(api_key=TPYTHON_API_KEY)
Client_OCR = CLIENT_OCR()
api_azure = Azzzure_API(Azure_Model=Azure_Model, api_key=Azure_API_KEY, azure_endpoint=Azure_Endpoint, api_version=Azure_API_Version)

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


@router.post("/exam/submit", response_model=Ai_ExamResult)
async def submit_exam(
    submission: Ai_ExamSubmission,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit exam answers, compare with the stored answer key, and return the result.
    Incorrect questions include the question text with the user's answer.
    """
    # Retrieve the exam record using the exam_id from the submission
    try:
        exam_record = await ai_exam_questions_collection.find_one({"_id": ObjectId(submission.exam_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid exam_id format")
        
    if not exam_record:
        raise HTTPException(status_code=404, detail="Exam record not found")
    
    # Ensure that the exam record belongs to the current user
    user_id = str(current_user.get("_id") or current_user.get("id"))
    if exam_record.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to submit this exam")
    
    exam_questions = exam_record.get("exam")
    if not isinstance(exam_questions, list):
        raise HTTPException(status_code=500, detail="Exam record format is invalid")
    
    if len(submission.responses) != len(exam_questions):
        raise HTTPException(
            status_code=400,
            detail="Number of responses does not match number of exam questions"
        )
    
    details = []
    score = 0
    for idx, question in enumerate(exam_questions):
        correct_answer = question.get("correct_answer")
        user_answer = submission.responses[idx]
        is_correct = user_answer == correct_answer
        detail = {
            "question_id": str(idx + 1),
            "correct_answer": correct_answer,
            "user_answer": user_answer,
            "is_correct": is_correct
        }
        if not is_correct:
            # Include the question text for incorrect responses
            detail["question"] = question.get("question")
        details.append(detail)
        if is_correct:
            score += 1

    result_obj = Ai_ExamResult(score=score, total=len(exam_questions), details=details)
    # save submission record
    submission_doc = {
        "user_id": user_id,
        "exam_id": submission.exam_id,
        "created_at": datetime.utcnow(),
        "result": result_obj.model_dump()
    }
    await ai_exam_submissions_collection.insert_one(submission_doc)

    return result_obj

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

# -----------------------------------------------------
# Submission History Route
# -----------------------------------------------------

@router.get("/exam/submission-history", response_model=List[AiSubmissionRecordOut])
async def list_submission_history(
    limit: int = Query(20, ge=1, le=100, description="Number of submission records to return"),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve the current user's previous exam submissions along with their results."""
    user_id = str(current_user.get("_id") or current_user.get("id"))
    submissions: List[AiSubmissionRecordOut] = []
    cursor = (
        ai_exam_submissions_collection.find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    async for doc in cursor:
        submissions.append(
            AiSubmissionRecordOut(
                id=str(doc["_id"]),
                exam_id=doc["exam_id"],
                created_at=doc["created_at"],
                result=Ai_ExamResult(**doc["result"])
            )
        )
    return submissions