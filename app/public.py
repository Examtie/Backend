from fastapi import APIRouter, Query, HTTPException
from typing import List
from bson import ObjectId

from app.models import ExamFileOut, ExamQuestion
from app.database import exam_files_collection, exam_questions_collection

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
