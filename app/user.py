from fastapi import APIRouter, Depends, Query, Body
from app.models import MeReturn,UpdateProfile, ExamFileOut, BookmarkCreate, BookmarkOut, ExamQuestion, ExamSubmissionCreate, ExamSubmissionOut, ExamAnswerCreate
from app.database import users_collection, exam_files_collection, bookmarks_collection, exam_questions_collection, exam_submissions_collection
from app.dependencies import get_current_user, require_roles, get_user_by_email
from typing import List, Any
from datetime import datetime

from app.settings import ALL_ROLES

router = APIRouter(
    prefix="/user/api/v1",
    tags=["User"]
)

@router.get("/@me", response_model=MeReturn)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return MeReturn(
        id=str(current_user["_id"]),
        email=current_user["email"],
        username=current_user["username"],
        full_name=current_user["full_name"],
        roles=current_user.get("roles", []),
        bio=current_user.get("bio", ""),
        profile_image=current_user.get("profile_image", "")
    )

@router.put("/@me", response_model=MeReturn)
async def update_profile(update: UpdateProfile, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if update_data:
        await users_collection.update_one({"_id": current_user["_id"]}, {"$set": update_data})
    updated_user = await get_user_by_email(current_user["email"])
    return MeReturn(
        id=str(updated_user["_id"]),
        email=updated_user["email"],
        username=updated_user["username"],
        full_name=updated_user.get("full_name", ""),
        roles=updated_user.get("roles", []),
        bio=updated_user.get("bio", ""),
        profile_image=updated_user.get("profile_image", "")
    )


@router.get("/dashboard")
async def dashboard(user: dict = Depends(require_roles(ALL_ROLES))):
    return {
        "message": f"Welcome {user.get('email')}!",
        "roles": user.get("roles", [])
    }

@router.get("/exams", response_model=List[ExamFileOut])
async def user_list_exams(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    skip = (page - 1) * limit
    files = []
    async for file_doc in exam_files_collection.find().skip(skip).limit(limit):
        files.append(ExamFileOut(
            id=str(file_doc["_id"]),
            title=file_doc["title"],
            description=file_doc["description"],
            tags=file_doc.get("tags", []),
            url=file_doc["url"],
            uploaded_by=file_doc["uploaded_by"],
            essay_count=file_doc.get("essay_count", 0),
            category_id=file_doc["category_id"],
            choice_count=file_doc.get("choice_count", 0)
        ))
    return files



@router.get("/exams/by-category/{category_id}", response_model=List[ExamFileOut])
async def user_list_exams_by_category(
    category_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    skip = (page - 1) * limit
    files = []
    async for file_doc in exam_files_collection.find({"category_id": category_id}).skip(skip).limit(limit):
        files.append(ExamFileOut(
            id=str(file_doc["_id"]),
            title=file_doc["title"],
            description=file_doc["description"],
            tags=file_doc.get("tags", []),
            url=file_doc["url"],
            uploaded_by=file_doc["uploaded_by"],
            category_id=file_doc["category_id"],
            essay_count=file_doc["essay_count"],
            choice_count=file_doc["choice_count"]
        ))
    return files

@router.post("/bookmarks", response_model=BookmarkOut)
async def add_bookmark(
    data: BookmarkCreate,
    current_user: dict = Depends(get_current_user)
):
    # Check if already bookmarked
    exists = await bookmarks_collection.find_one({"user_id": str(current_user["_id"]), "exam_id": data.exam_id})
    if exists:
        raise Exception("Already bookmarked")
    doc = {
        "user_id": str(current_user["_id"]),
        "exam_id": data.exam_id,
        "created_at": datetime.utcnow()
    }
    result = await bookmarks_collection.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return BookmarkOut(**doc)

@router.delete("/bookmarks/{exam_id}")
async def remove_bookmark(
    exam_id: str,
    current_user: dict = Depends(get_current_user)
):
    result = await bookmarks_collection.delete_one({"user_id": str(current_user["_id"]), "exam_id": exam_id})
    if result.deleted_count == 0:
        raise Exception("Bookmark not found")
    return {"message": "Bookmark removed"}

@router.get("/bookmarks", response_model=List[BookmarkOut])
async def list_bookmarks(current_user: dict = Depends(get_current_user)):
    bookmarks = []
    async for doc in bookmarks_collection.find({"user_id": str(current_user["_id"])}):
        doc["id"] = str(doc["_id"])
        bookmarks.append(BookmarkOut(**doc))
    return bookmarks

@router.get("/exams/{exam_id}/questions", response_model=List[dict])
async def get_exam_questions(exam_id: str):
    questions = []
    async for q in exam_questions_collection.find({"exam_id": exam_id}):
        q["id"] = str(q["_id"])
        del q["_id"]
        questions.append(q)
    return questions

@router.post("/exams/{exam_id}/submit")
async def submit_exam(
    exam_id: str,
    submission: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    # Save submission
    doc = {
        "user_id": str(current_user["_id"]),
        "exam_id": exam_id,
        "answers": submission.get("answers", []),
        "submitted_at": datetime.utcnow()
    }
    result = await exam_submissions_collection.insert_one(doc)
    return {"submission_id": str(result.inserted_id), "exam_id": exam_id}
