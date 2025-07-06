from fastapi import APIRouter, Depends, Query, Body, HTTPException
from bson import ObjectId
from app.models import MeReturn, UpdateProfile, ExamFileOut, BookmarkCreate, BookmarkOut, ExamQuestion, ExamSubmissionCreate, ExamSubmissionOut, ExamAnswerCreate, ExamCategoryOut
from app.database import users_collection, exam_files_collection, bookmarks_collection, exam_questions_collection, exam_submissions_collection, exam_categories_collection
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
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await users_collection.update_one({"_id": current_user["_id"]}, {"$set": update_data})
    updated_user = await get_user_by_email(current_user["email"])
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
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
async def dashboard(user: dict = Depends(require_roles("user"))):
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
            essay_count=file_doc.get("essay_count", 0),
            choice_count=file_doc.get("choice_count", 0)
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
    # Check if there's an existing draft to update
    existing_draft = await exam_submissions_collection.find_one({
        "user_id": str(current_user["_id"]),
        "exam_id": exam_id,
        "is_draft": True
    })
    
    doc = {
        "user_id": str(current_user["_id"]),
        "exam_id": exam_id,
        "answers": submission.get("answers", []),
        "submitted_at": datetime.utcnow(),
        "time_spent": submission.get("time_spent", 0),
        "is_draft": False
    }
    
    if existing_draft:
        # Update existing draft to completed submission
        await exam_submissions_collection.update_one(
            {"_id": existing_draft["_id"]},
            {"$set": doc}
        )
        return {"submission_id": str(existing_draft["_id"]), "exam_id": exam_id}
    else:
        # Create new submission
        result = await exam_submissions_collection.insert_one(doc)
        return {"submission_id": str(result.inserted_id), "exam_id": exam_id}

@router.post("/exams/{exam_id}/save-progress")
async def save_exam_progress(
    exam_id: str,
    submission: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Save exam progress (auto-save functionality)"""
    # Check if there's an existing progress save
    existing = await exam_submissions_collection.find_one({
        "user_id": str(current_user["_id"]),
        "exam_id": exam_id,
        "is_draft": True
    })
    
    doc = {
        "user_id": str(current_user["_id"]),
        "exam_id": exam_id,
        "answers": submission.get("answers", []),
        "is_draft": submission.get("is_draft", True),
        "saved_at": datetime.utcnow(),
        "time_spent": submission.get("time_spent", 0)
    }
    
    if existing:
        # Update existing draft
        await exam_submissions_collection.update_one(
            {"_id": existing["_id"]},
            {"$set": doc}
        )
        return {"message": "Progress saved", "submission_id": str(existing["_id"])}
    else:
        # Create new draft
        result = await exam_submissions_collection.insert_one(doc)
        return {"message": "Progress saved", "submission_id": str(result.inserted_id)}

# === EXAM CATEGORY MANAGEMENT FOR USERS ===
@router.get("/exam-categories", response_model=List[ExamCategoryOut])
async def user_list_exam_categories():
    categories = []
    async for cat in exam_categories_collection.find():
        categories.append(ExamCategoryOut(
            id=str(cat["_id"]),
            name=cat["name"],
            description=cat.get("description", ""),
            english_name=cat.get("english_name", "")
        ))
    return categories

@router.get("/exam-categories/{category_id}", response_model=ExamCategoryOut)
async def user_get_exam_category(category_id: str):
    try:
        oid = ObjectId(category_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid category ID format")
    cat = await exam_categories_collection.find_one({"_id": oid})
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return ExamCategoryOut(
        id=str(cat["_id"]),
        name=cat["name"],
        description=cat.get("description", ""),
        english_name=cat.get("english_name", "")
    )

@router.get("/exams-with-progress", response_model=List[dict])
async def user_list_exams_with_progress(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user)
):
    """Get exams with user's progress information"""
    skip = (page - 1) * limit
    files = []
    
    async for file_doc in exam_files_collection.find().skip(skip).limit(limit):
        exam_file = {
            "id": str(file_doc["_id"]),
            "title": file_doc["title"],
            "description": file_doc["description"],
            "tags": file_doc.get("tags", []),
            "url": file_doc["url"],
            "uploaded_by": file_doc["uploaded_by"],
            "essay_count": file_doc.get("essay_count", 0),
            "choice_count": file_doc.get("choice_count", 0),
            "progress": None,
            "is_completed": False
        }
        
        # Check for submissions (completed or draft)
        submission = await exam_submissions_collection.find_one({
            "user_id": str(current_user["_id"]),
            "exam_id": str(file_doc["_id"])
        }, sort=[("submitted_at", -1), ("saved_at", -1)])
        
        if submission:
            total_questions = file_doc.get("essay_count", 0) + file_doc.get("choice_count", 0)
            answered_count = len([a for a in submission.get("answers", []) if a.get("answer") and str(a.get("answer")).strip()])
            
            exam_file["progress"] = {
                "answered_count": answered_count,
                "total_questions": total_questions,
                "percentage": (answered_count / total_questions * 100) if total_questions > 0 else 0,
                "last_updated": submission.get("saved_at") or submission.get("submitted_at"),
                "is_draft": submission.get("is_draft", False)
            }
            exam_file["is_completed"] = not submission.get("is_draft", False) and submission.get("submitted_at") is not None
        
        files.append(exam_file)
    
    return files

# === EXAM PROGRESS MANAGEMENT ===
@router.get("/exam-progress")
async def get_exam_progress(current_user: dict = Depends(get_current_user)):
    """Get user's exam progress for all exams"""
    progress_data = []
    
    async for submission in exam_submissions_collection.find({"user_id": str(current_user["_id"])}):
        exam_id = submission["exam_id"]
        
        # Get exam file to calculate total questions
        exam_file = await exam_files_collection.find_one({"_id": ObjectId(exam_id)})
        if not exam_file:
            continue
            
        total_questions = exam_file.get("essay_count", 0) + exam_file.get("choice_count", 0)
        answered_count = len([a for a in submission.get("answers", []) if a.get("answer") and str(a.get("answer")).strip()])
        
        progress_data.append({
            "exam_id": exam_id,
            "progress_percentage": (answered_count / total_questions * 100) if total_questions > 0 else 0,
            "answered_count": answered_count,
            "total_questions": total_questions,
            "last_attempted": submission.get("saved_at") or submission.get("submitted_at"),
            "is_completed": not submission.get("is_draft", False) and submission.get("submitted_at") is not None,
            "time_spent": submission.get("time_spent", 0)
        })
    
    return progress_data

@router.get("/exams/in-progress", response_model=List[dict])
async def get_in_progress_exams(current_user: dict = Depends(get_current_user)):
    """Get all exams that are currently in progress (drafts with answers)"""
    in_progress_exams = []
    
    # Find all draft submissions with answers
    async for submission in exam_submissions_collection.find({
        "user_id": str(current_user["_id"]),
        "is_draft": True,
        "answers": {"$exists": True, "$ne": []}
    }).sort("saved_at", -1):
        
        exam_id = submission["exam_id"]
        
        # Get exam file details
        try:
            exam_file = await exam_files_collection.find_one({"_id": ObjectId(exam_id)})
            if not exam_file:
                continue
                
            total_questions = exam_file.get("essay_count", 0) + exam_file.get("choice_count", 0)
            answered_count = len([a for a in submission.get("answers", []) if a.get("answer") and str(a.get("answer")).strip()])
            
            # Only include if there are actual answers
            if answered_count > 0:
                in_progress_exams.append({
                    "exam_id": exam_id,
                    "title": exam_file["title"],
                    "description": exam_file["description"],
                    "tags": exam_file.get("tags", []),
                    "url": exam_file["url"],
                    "essay_count": exam_file.get("essay_count", 0),
                    "choice_count": exam_file.get("choice_count", 0),
                    "progress_percentage": (answered_count / total_questions * 100) if total_questions > 0 else 0,
                    "answered_count": answered_count,
                    "total_questions": total_questions,
                    "last_saved": submission.get("saved_at"),
                    "time_spent": submission.get("time_spent", 0),
                    "submission_id": str(submission["_id"])
                })
        except Exception as e:
            print(f"Error processing exam {exam_id}: {e}")
            continue
    
    return in_progress_exams

@router.delete("/exams/{exam_id}/progress")
async def clear_exam_progress(
    exam_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Clear saved progress for an exam (delete draft)"""
    try:
        result = await exam_submissions_collection.delete_one({
            "user_id": str(current_user["_id"]),
            "exam_id": exam_id,
            "is_draft": True
        })
        
        if result.deleted_count > 0:
            return {"message": "Progress cleared successfully"}
        else:
            return {"message": "No progress found to clear"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear progress: {str(e)}")

@router.post("/exams/{exam_id}/update-activity")
async def update_exam_activity(
    exam_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Update user's last activity timestamp for an exam"""
    try:
        # Update or create activity record
        await exam_submissions_collection.update_one(
            {
                "user_id": str(current_user["_id"]),
                "exam_id": exam_id,
                "is_draft": True
            },
            {
                "$set": {
                    "last_activity": datetime.utcnow()
                }
            },
            upsert=False  # Only update if exists
        )
        
        return {"message": "Activity updated"}
    except Exception as e:
        # Don't fail the request if activity update fails
        return {"message": "Activity update skipped"}
