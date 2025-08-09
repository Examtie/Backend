from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query, Header
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from app.models import Flashcard, FlashcardRecordOut, ExamQuestion, ExamRecordOut, Ai_ExamSubmission, Ai_ExamResult, AiSubmissionRecordOut
from app.dependencies import get_current_user
from app.database import flashcards_collection, ai_exam_questions_collection, ai_exam_submissions_collection
from app.settings import Azure_API_KEY, Azure_Endpoint, Azure_API_Version, Azure_Model
import uuid

from ai_runner.Typhoon import Typhoon_API
from ai_runner.PDFExtrack import CLIENT_OCR
from ai_runner.AAzure import Azzzure_API

# New provider clients
from openai import OpenAI
import requests
import json

from app.rate_limit import rate_limit_dependency

router = APIRouter(
    prefix="/ai/api/v1",
    tags=["ai"],
)

Client_OCR = CLIENT_OCR()
api_azure = Azzzure_API(Azure_Model=Azure_Model, api_key=Azure_API_KEY, azure_endpoint=Azure_Endpoint, api_version=Azure_API_Version)


def _choose_provider(
    provider: Optional[str],
    api_key: Optional[str],
    model: Optional[str],
    base_url: Optional[str],
):
    """
    Returns a callable with shape generate_flashcards(context, amount) and generate_exam_questions(context, amount)
    for the chosen provider. Supported providers:
    - azure (uses existing Azzzure_API, ignores base_url)
    - openrouter (OpenAI-compatible)
    - cerebras (OpenAI-compatible)
    - openai_compatible (custom base_url)
    - ollama (OpenAI-compatible base_url like http://localhost:11434)
    - gemini (Google Generative Language API)
    Fallback to azure default config if not specified.
    """

    provider = (provider or "").lower()

    if provider in ("", "azure"):
        # Allow BYO Azure via provided api_key/base_url/model
        if api_key or base_url or model:
            return Azzzure_API(
                Azure_Model=model or Azure_Model,
                api_key=api_key or Azure_API_KEY,
                azure_endpoint=base_url or Azure_Endpoint,
                api_version=Azure_API_Version,
            )
        return api_azure

    if provider in ("openrouter", "cerebras", "openai_compatible", "ollama"):
        if not api_key:
            raise HTTPException(status_code=400, detail="API key is required for this provider")
        if provider == "openrouter" and not base_url:
            base_url = "https://openrouter.ai/api/v1"
        if provider == "cerebras" and not base_url:
            base_url = "https://api.cerebras.ai/v1"

        # Normalize OpenAI-compatible base_url to include /v1 suffix
        if base_url:
            bu = base_url.strip()
            if not bu.endswith("/"):
                bu = bu
            # Append /v1 if not present as a path segment
            if not bu.rstrip("/").endswith("/v1"):
                bu = bu.rstrip("/") + "/v1"
            base_url = bu

        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        used_model = model or "gpt-4o-mini"

        def _call(prompt: str, system_prompt: str):
            resp = client.chat.completions.create(
                model=used_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            content = resp.choices[0].message.content or ""
            # Try to parse JSON block if fenced
            if isinstance(content, str) and content.strip().startswith("```json"):
                content = content.split("```json")[-1].rsplit("```", 1)[0].strip()
            try:
                return json.loads(content)
            except Exception:
                # Best-effort simple extraction of JSON brackets
                start = content.find("[")
                end = content.rfind("]")
                if start != -1 and end != -1 and end > start:
                    return json.loads(content[start : end + 1])
                raise HTTPException(status_code=502, detail="Invalid JSON from model")

        class Adapter:
            def generate_exam_questions(self, context: str, amount: int = 10):
                return _call(f"สร้างข้อสอบจำนวน  {amount} ข้อ และข้อสอบเนื้อหาเกี่ยวกับ : {context}", api_azure.pdf_to_exam_system)

            def generate_flashcards(self, context: str, amount: int = 10):
                return _call(f"สร้างแฟรการ์ด เกี่ยวกับ {context} มัธยมศึกษาปีที่ 5 \nจำนวน {amount} แฟรชการ์ด.", api_azure.flashcard_from_prompt)

        return Adapter()

    if provider == "gemini":
        if not api_key:
            raise HTTPException(status_code=400, detail="API key is required for Gemini")
        # Simple REST call to Gemini 1.5 Pro style generateContent
        used_model = model or "gemini-1.5-flash"

        def _gemini_call(prompt: str, system_prompt: str):
            url = f"https://generativelanguage.googleapis.com/v1/models/{used_model}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": system_prompt + "\n\n" + prompt}]}
                ]
            }
            r = requests.post(url, json=payload, timeout=60)
            if r.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Gemini error: {r.text}")
            data = r.json()
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"] or ""
            except Exception:
                raise HTTPException(status_code=502, detail="Unexpected Gemini response")
            if isinstance(text, str) and text.strip().startswith("```json"):
                text = text.split("```json")[-1].rsplit("```", 1)[0].strip()
            try:
                return json.loads(text)
            except Exception:
                start = text.find("[")
                end = text.rfind("]")
                if start != -1 and end != -1 and end > start:
                    return json.loads(text[start : end + 1])
                raise HTTPException(status_code=502, detail="Invalid JSON from Gemini")

        class GAdapter:
            def generate_exam_questions(self, context: str, amount: int = 10):
                return _gemini_call(f"สร้างข้อสอบจำนวน  {amount} ข้อ และข้อสอบเนื้อหาเกี่ยวกับ : {context}", api_azure.pdf_to_exam_system)

            def generate_flashcards(self, context: str, amount: int = 10):
                return _gemini_call(f"สร้างแฟรการ์ด เกี่ยวกับ {context} มัธยมศึกษาปีที่ 5 \nจำนวน {amount} แฟรชการ์ด.", api_azure.flashcard_from_prompt)

        return GAdapter()

    # Default fallback
    return api_azure


    @router.post("/provider/test", dependencies=[Depends(rate_limit_dependency)])
    async def test_provider_settings(
        current_user: dict = Depends(get_current_user),
        x_provider: str | None = Header(None, alias="X-Provider"),
        x_api_key: str | None = Header(None, alias="X-API-Key"),
        x_model: str | None = Header(None, alias="X-Model"),
        x_base_url: str | None = Header(None, alias="X-Base-Url"),
    ):
        """Quickly validate BYO provider headers by doing a minimal no-op request.
        For Azure: uses server default unless BYO is specified. Returns { status: 'ok' } if credentials look valid.
        """
        try:
            adapter = _choose_provider(x_provider, x_api_key, x_model, x_base_url)
            # perform a tiny probe with a deterministic minimal prompt
            probe = None
            try:
                probe = adapter.generate_flashcards(context="test connectivity", amount=1)
            except HTTPException:
                raise
            except Exception as e:
                # Normalize provider errors
                raise HTTPException(status_code=502, detail=f"Provider error: {str(e)[:200]}")

            # Accept either list or dict with flashcards
            if isinstance(probe, list):
                return {"status": "ok"}
            if isinstance(probe, dict) and ("flashcards" in probe):
                return {"status": "ok"}
            # Some providers may return empty or unexpected payloads; if no exception it still indicates validity
            return {"status": "ok"}
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

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
async def _generate_flashcard(pdf_bytes = None, prompt: Optional[str] = None, amount: int = 10, provider_adapter=None):
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

    adapter = provider_adapter or api_azure
    data = adapter.generate_flashcards(context=context, amount=amount)
    print(data)

    return data

# -----------------------------------------------------
# Helper – generate exam questions
# -----------------------------------------------------
async def _generate_exam(pdf_bytes = None, prompt: Optional[str] = None, amount: int = 10, provider_adapter=None):
    if not pdf_bytes and not prompt:
        raise HTTPException(status_code=400, detail="Either PDF bytes or prompt must be provided")
    if pdf_bytes:
        print("Processing PDF bytes for exam generation...")
        context = Client_OCR.ocr(pdf_bytes=pdf_bytes)
    else:
        context = prompt
    if not context:
        raise HTTPException(status_code=400, detail="No context available for exam generation")

    adapter = provider_adapter or api_azure
    questions = adapter.generate_exam_questions(context=context, amount=amount)
    return questions

# -----------------------------------------------------
# Routes
# -------------------------------------------------ไ----

@router.post("/flashcards/generate-pdf", response_model=List[Flashcard], dependencies=[Depends(rate_limit_dependency)])
async def generate_flashcards_pdf(
    file: UploadFile = File(None, description="Optional PDF file to convert into flashcards"),
    amount: int = Query(10, ge=1, le=100, description="Number of flashcards to generate"),
    current_user: dict = Depends(get_current_user),
    x_provider: str | None = Header(None, alias="X-Provider"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    x_model: str | None = Header(None, alias="X-Model"),
    x_base_url: str | None = Header(None, alias="X-Base-Url"),
):
    """Upload a PDF, run OCR & LLM pipeline, and return generated flashcards."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a PDF")

    pdf_bytes = await file.read()

    adapter = _choose_provider(x_provider, x_api_key, x_model, x_base_url)
    flashcards_data = await _generate_flashcard(pdf_bytes=pdf_bytes, amount=amount, provider_adapter=adapter)
    # Normalize to list
    if isinstance(flashcards_data, dict) and "flashcards" in flashcards_data:
        fc_list = flashcards_data["flashcards"]
    elif isinstance(flashcards_data, list):
        fc_list = flashcards_data
    else:
        raise HTTPException(status_code=502, detail="Unexpected flashcards response format")

    # Store history record
    record = {
        "user_id": str(current_user.get("_id") or current_user.get("id")),
        "filename": file.filename,
        "created_at": datetime.utcnow(),
        "flashcards": fc_list,
    }
    result = await flashcards_collection.insert_one(record)

    return fc_list

@router.post("/flashcards/generate-text", response_model=List[Flashcard], dependencies=[Depends(rate_limit_dependency)])
async def generate_flashcards_text(
    amount: int = Query(10, ge=1, le=100, description="Number of flashcards to generate"),
    prompt: str = Query(None, description="Optional prompt to guide flashcard generation"),
    current_user: dict = Depends(get_current_user),
    x_provider: str | None = Header(None, alias="X-Provider"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    x_model: str | None = Header(None, alias="X-Model"),
    x_base_url: str | None = Header(None, alias="X-Base-Url"),
):

    adapter = _choose_provider(x_provider, x_api_key, x_model, x_base_url)
    flashcards_data = await _generate_flashcard(prompt=prompt, amount=amount, provider_adapter=adapter)
    if isinstance(flashcards_data, dict) and "flashcards" in flashcards_data:
        fc_list = flashcards_data["flashcards"]
    elif isinstance(flashcards_data, list):
        fc_list = flashcards_data
    else:
        raise HTTPException(status_code=502, detail="Unexpected flashcards response format")
    
    record = {
        "user_id": str(current_user.get("_id") or current_user.get("id")),
        "prompt": prompt,
        "created_at": datetime.utcnow(),
        "flashcards": fc_list,
    }
    result = await flashcards_collection.insert_one(record)

    return fc_list

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

@router.post("/exam/generate-pdf", response_model=List[ExamQuestion], dependencies=[Depends(rate_limit_dependency)])
async def generate_exam_questions_pdf(
    file: UploadFile = File(None, description="Optional PDF file to convert into exam questions"),
    amount: int = Query(5, ge=1, le=100, description="Number of exam questions to generate"),
    current_user: dict = Depends(get_current_user),
    x_provider: str | None = Header(None, alias="X-Provider"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    x_model: str | None = Header(None, alias="X-Model"),
    x_base_url: str | None = Header(None, alias="X-Base-Url"),
):
    """Upload a PDF, run OCR & LLM pipeline, and return generated exam questions."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a PDF")

    pdf_bytes = await file.read()

    adapter = _choose_provider(x_provider, x_api_key, x_model, x_base_url)
    exam_data = await _generate_exam(pdf_bytes=pdf_bytes, amount=amount, provider_adapter=adapter)
    if not isinstance(exam_data, list):
        raise HTTPException(status_code=502, detail="Unexpected exam response format")

    record = {
        "user_id": str(current_user.get("_id") or current_user.get("id")),
        "filename": file.filename,
        "created_at": datetime.utcnow(),
        "exam": exam_data,
    }
    await ai_exam_questions_collection.insert_one(record)

    return [ExamQuestion(id=str(i + 1), type="multiple_choice", question=q.get("question"), choices=q.get("options"), answer=q.get("correct_answer")) for i, q in enumerate(exam_data)]


@router.post("/exam/generate-text", response_model=Dict[str, Any], dependencies=[Depends(rate_limit_dependency)])
async def generate_exam_questions_text(
    amount: int = Query(5, ge=1, le=100, description="Number of exam questions to generate"),
    prompt: str = Query(None, description="Optional prompt to guide exam question generation"),
    current_user: dict = Depends(get_current_user),
    x_provider: str | None = Header(None, alias="X-Provider"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    x_model: str | None = Header(None, alias="X-Model"),
    x_base_url: str | None = Header(None, alias="X-Base-Url"),
):
    """Generate exam questions based on a text prompt."""
    adapter = _choose_provider(x_provider, x_api_key, x_model, x_base_url)
    exam_data = await _generate_exam(prompt=prompt, amount=amount, provider_adapter=adapter)
    
    # Ensure that exam_data is iterable (i.e. a list)
    if not isinstance(exam_data, list):
        raise HTTPException(
            status_code=500,
            detail="Exam question generation failed: Unexpected response format."
        )

    generation_id = str(uuid.uuid4())

    record = {
        "generation_id": generation_id,
        "user_id": str(current_user.get("_id") or current_user.get("id")),
        "prompt": prompt,
        "created_at": datetime.utcnow(),
        "exam": exam_data,
    }
    await ai_exam_questions_collection.insert_one(record)

    return {
        "generation_id": generation_id,
        "questions": [
            ExamQuestion(
                id=str(i + 1),
                type="multiple_choice",
                question=q.get("question"),
                choices=q.get("options"),
            answer=q.get("correct_answer"),
            why_answer_this_one=q.get("why_answer_this_one"),
            what_do_i_read=q.get("what_do_i_read")
        )
        for i, q in enumerate(exam_data)
    ]}


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
        exam_record = await ai_exam_questions_collection.find_one({"generation_id": submission.exam_id})
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
        # Always include question text and explanations in the response
        detail = {
            "question_id": str(idx + 1),
            "question": question.get("question"),
            "correct_answer": correct_answer,
            "user_answer": user_answer,
            "is_correct": is_correct,
            "why_answer_this_one": question.get("why_answer_this_one") or question.get("Why_answer_this_one"),
            "what_do_i_read": question.get("what_do_i_read")
        }
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