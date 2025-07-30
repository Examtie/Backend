from fastapi import APIRouter, Query, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict, Any
from bson import ObjectId

from app.models import (
    ExamFileOut,
    ExamQuestion,
    ExamSubmissionCreate,
    ExamAnswerOut,
    ExamTextOut,
    ExamCheckResult,
    ExamCategoryOut
)
from app.database import exam_files_collection, exam_questions_collection, exam_texts_collection, redis_client, exam_categories_collection
from app.settings import CACHE_EXPIRE_SECONDS

router = APIRouter(
    prefix="/public/api/v1",
    tags=["Public"]
)

@router.get("/exams", response_model=List[ExamFileOut])
async def list_exams(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    """Return paginated list of exams - no authentication required."""
    skip = (page - 1) * limit
    files: List[ExamFileOut] = []
    async for file_doc in exam_files_collection.find().skip(skip).limit(limit):
        files.append(
            ExamFileOut(
                id=str(file_doc["_id"]),
                title=file_doc["title"],
                description=file_doc.get("description", ""),
                tags=file_doc.get("tags", []),
                url=file_doc["url"],
                uploaded_by=file_doc.get("uploaded_by"),
                essay_count=file_doc.get("essay_count", 0),
                choice_count=file_doc.get("choice_count", 0),
            )
        )
    return files

@router.get("/exams/{exam_id}/questions", response_model=List[ExamQuestion])
async def get_exam_questions_public(exam_id: str):
    """Return questions for an exam - no authentication required."""
    questions: List[ExamQuestion] = []
    async for qdoc in exam_questions_collection.find({"exam_id": exam_id}).sort("_id"):
        questions.append(
            ExamQuestion(
                id=str(qdoc["_id"]),

                type=qdoc["type"],
                question=qdoc["question"],
                choices=qdoc.get("choices"),
                answer=qdoc.get("answer"),
            )
        )
    if not questions:
        raise HTTPException(status_code=404, detail="Questions not found")
    return questions

@router.get("/exam-categories", response_model=List[ExamCategoryOut])
async def public_list_exam_categories():
    """Return all exam categories - no authentication required."""
    cache_key = "exam_categories:all"
    cached = await redis_client.get(cache_key)
    if cached:
        from bson import json_util
        return [ExamCategoryOut(**cat) for cat in json_util.loads(cached)]
    
    categories = []
    async for cat in exam_categories_collection.find():
        categories.append(ExamCategoryOut(
            id=str(cat["_id"]),
            name=cat["name"],
            description=cat.get("description", ""),
            english_name=cat.get("english_name", "")
        ).model_dump())
        
    from bson import json_util
    await redis_client.set(cache_key, json_util.dumps(categories), ex=CACHE_EXPIRE_SECONDS)
    return [ExamCategoryOut(**cat) for cat in categories]

# === MARKET ===
from app.market import to_market_item_out, market_items_collection, MarketItemOut

@router.get("/market/items", response_model=List[MarketItemOut])
async def public_list_market_items(q: int = Query(10, ge=1, le=100, description="Number of items to retrieve")):
    """Public list of market items."""
    items: List[MarketItemOut] = []
    async for doc in market_items_collection.find().limit(q):
        items.append(to_market_item_out(doc))
    return items

@router.get("/market/items/search", response_model=List[MarketItemOut])
async def public_search_market_items(
    keyword: str = Query(..., min_length=1, description="Keyword to search for"),
    limit: int = Query(20, ge=1, le=100, description="Max items to return"),
):
    """Public search of market items by keyword."""
    query = {
        "$or": [
            {"name": {"$regex": keyword, "$options": "i"}},
            {"description": {"$regex": keyword, "$options": "i"}},
        ]
    }
    items: List[MarketItemOut] = []
    async for doc in market_items_collection.find(query).limit(limit):
        items.append(to_market_item_out(doc))
    return items

# === EXAM SUBMISSION ===


@router.get("/exams/{exam_id}/text", response_model=ExamTextOut)
async def get_exam_extracted_text(exam_id: str):
    cache_key = f"exam_text:{exam_id}"
    cached = await redis_client.get(cache_key)
    if cached is not None:
        return ExamTextOut(exam_id=exam_id, text=cached)
    doc = await exam_texts_collection.find_one({"exam_id": exam_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Extracted text not found")
    text = doc.get("text", "")
    await redis_client.set(cache_key, text, ex=1800)  # cache 30min
    return ExamTextOut(exam_id=exam_id, text=text)


@router.post("/exams/{exam_id}/submit", response_model=ExamCheckResult)
async def submit_exam_and_check(exam_id: str, submission: ExamSubmissionCreate = Body(...)):
    """Accepts user's answers, compares with answer key, and returns result."""
    if submission.exam_id != exam_id:
        raise HTTPException(status_code=400, detail="exam_id in path and body mismatch")

    # Map answers for quick lookup
    answer_map: Dict[str, Any] = {ans.question_id: ans.answer for ans in submission.answers}

    total = await exam_questions_collection.count_documents({"exam_id": exam_id})
    questions_cursor = exam_questions_collection.find({"exam_id": exam_id})

    correct = 0
    details: List[ExamAnswerOut] = []

    async for qdoc in questions_cursor:
        qid = str(qdoc["_id"])
        correct_answer = qdoc.get("answer")
        user_answer = answer_map.get(qid)
        is_correct = False
        if user_answer is not None and correct_answer is not None:
            if isinstance(correct_answer, list):
                # Normalize lists (e.g., sort for unordered multiple selections)
                is_correct = sorted(correct_answer) == sorted(user_answer) if isinstance(user_answer, list) else False
            else:
                # For strings: case-insensitive compare after stripping spaces
                is_correct = str(correct_answer).strip().lower() == str(user_answer).strip().lower()
        if is_correct:
            correct += 1
        details.append(
            ExamAnswerOut(
                question_id=qid,
                answer=user_answer,
                is_correct=is_correct,
            )
        )

    wrong = total - correct
    return ExamCheckResult(total=total, correct=correct, wrong=wrong, details=details)

@router.get("/market/items/{item_id}", response_model=MarketItemOut)
async def public_get_market_item(item_id: str):
    """Retrieve a single market item by its *id* (public)."""
    try:
        oid = ObjectId(item_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid item ID format")

    doc = await market_items_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Item not found")
    return to_market_item_out(doc)
