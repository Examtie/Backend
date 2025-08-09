#!/usr/bin/env python3
"""
Simple test server for exam submission functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

app = FastAPI(title="Examtie Test API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# Simple models
class ExamAnswerCreate(BaseModel):
    question_id: str
    answer: str | List[str]

class ExamSubmissionCreate(BaseModel):
    exam_id: str
    answers: List[ExamAnswerCreate]

class ExamCheckResult(BaseModel):
    total: int
    correct: int
    wrong: int
    details: List[Dict[str, Any]]

class Ai_ExamResult(BaseModel):
    score: int
    total: int
    details: List[Dict[str, Any]]

# Mock exam data
MOCK_EXAM_DATA = [
    {
        "question": "ถ้ามีลูกบอลสีแดง 4 ลูกและสีน้ำเงิน 6 ลูกในกล่อง จะสุ่มหยิบลูกบอล 1 ลูก ความน่าจะเป็นที่หยิบได้ลูกบอลสีแดงคือข้อใด?",
        "options": ["A) 1/2", "B) 2/5", "C) 3/5", "D) 4/7"],
        "why_answer_this_one": "ลูกบอลทั้งหมด 4+6=10 ลูก ความน่าจะเป็นที่ได้สีแดงคือ 4/10 = 2/5 ดังนั้นคำตอบคือ B",
        "correct_answer": "B"
    },
    {
        "question": "เมื่อต้องการสุ่มเลือกตัวอักษรจากคำว่า 'MATH' ความน่าจะเป็นที่จะเลือกได้ตัวอักษร 'A' คือข้อใด?",
        "options": ["A) 1/4", "B) 1/5", "C) 1/6", "D) 1/3"],
        "why_answer_this_one": "มีตัวอักษร 4 ตัว (M, A, T, H) โอกาสได้ A คือ 1/4 ตอบข้อ A",
        "correct_answer": "A"
    },
    {
        "question": "ทอยลูกเต๋าหนึ่งลูก ความน่าจะเป็นที่ผลออกมากกว่า 4 เท่ากับเท่าไหร่?",
        "options": ["A) 1/6", "B) 1/3", "C) 2/3", "D) 1/2"],
        "why_answer_this_one": "หน้าที่มากกว่า 4 คือ 5, 6 มี 2 หน้า จาก 6 หน้า 2/6 = 1/3 ตอบข้อ B",
        "correct_answer": "B"
    }
]

@app.get("/")
async def root():
    return {"message": "Examtie Test API is running"}

@app.get("/api/mock/get-exam")
async def get_mock_exam():
    """Return mock exam questions without answers"""
    questions = []
    for i, q in enumerate(MOCK_EXAM_DATA, 1):
        questions.append({
            "id": str(i),
            "type": "multiple_choice",
            "question": q["question"],
            "choices": q["options"]
        })
    return questions

@app.post("/api/mock/submit", response_model=Ai_ExamResult)
async def submit_mock_exam(payload: ExamSubmissionCreate):
    """Submit mock exam and get results"""
    
    if len(payload.answers) != len(MOCK_EXAM_DATA):
        raise HTTPException(
            status_code=400,
            detail="Number of responses does not match number of exam questions."
        )

    score = 0
    details = []
    answer_map = {ans.question_id: ans.answer for ans in payload.answers}

    for idx, q in enumerate(MOCK_EXAM_DATA, start=1):
        correct = q["correct_answer"]
        user_ans = answer_map.get(str(idx), "")
        is_correct = str(user_ans).upper().strip() == correct.upper().strip()
        
        if is_correct:
            score += 1
            
        detail = {
            "question_id": str(idx),
            "user_answer": user_ans,
            "correct_answer": correct,
            "is_correct": is_correct,
            "question": q["question"]
        }
        
        if not is_correct:
            detail["why_answer_this_one"] = q["why_answer_this_one"]
            
        details.append(detail)

    return Ai_ExamResult(score=score, total=len(MOCK_EXAM_DATA), details=details)

@app.post("/api/public/api/v1/exams/{exam_id}/submit", response_model=ExamCheckResult)
async def submit_public_exam(exam_id: str, payload: ExamSubmissionCreate):
    """Public exam submission endpoint (for testing)"""
    
    # For demo purposes, return mock results
    score = 2
    total = 3
    details = []
    
    for i, ans in enumerate(payload.answers, 1):
        details.append({
            "question_id": ans.question_id,
            "answer": ans.answer,
            "is_correct": i <= score,
            "correct_answer": f"Answer {i}"
        })
    
    return ExamCheckResult(
        total=total,
        correct=score,
        wrong=total - score,
        details=details
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
