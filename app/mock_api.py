from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Dict, Any

# Re-use central models
from app.models import ExamQuestion, ExamAnswerCreate, ExamSubmissionCreate, Ai_ExamResult, ExamFileOut

# -----------------------------
# Mock Exam Dataset (in-memory)
# -----------------------------
EXAM_DATA: List[Dict[str, Any]] = [
    {
        "question": "ถ้ามีลูกบอลสีแดง $$4$$ ลูกและสีน้ำเงิน $$6$$ ลูกในกล่อง จะสุ่มหยิบลูกบอล $$1$$ ลูก ความน่าจะเป็นที่หยิบได้ลูกบอลสีแดงคือข้อใด?",
        "options": [
            "A) $$\\dfrac{1}{2}$$",
            "B) $$\\dfrac{2}{5}$$",
            "C) $$\\dfrac{3}{5}$$",
            "D) $$\\dfrac{4}{7}$$",
        ],
        "Why_answer_this_one": "ลูกบอลทั้งหมด $$4+6=10$$ ลูก ความน่าจะเป็นที่ได้สีแดงคือ $$\\dfrac{4}{10} = \\dfrac{2}{5}$$ ดังนั้นคำตอบคือ B",
        "correct_answer": "B",
    },
    {
        "question": "เมื่อต้องการสุ่มเลือกตัวอักษรจากคำว่า 'MATH' ความน่าจะเป็นที่จะเลือกได้ตัวอักษร 'A' คือข้อใด?",
        "options": [
            "A) $$\\dfrac{1}{4}$$",
            "B) $$\\dfrac{1}{5}$$",
            "C) $$\\dfrac{1}{6}$$",
            "D) $$\\dfrac{1}{3}$$",
        ],
        "Why_answer_this_one": "มีตัวอักษร 4 ตัว (M, A, T, H) โอกาสได้ A คือ $$\\dfrac{1}{4}$$ ตอบข้อ A",
        "correct_answer": "A",
    },
    {
        "question": "ทอยลูกเต๋าหนึ่งลูก ความน่าจะเป็นที่ผลออกมากกว่า $$4$$ เท่ากับเท่าไหร่?",
        "options": [
            "A) $$\\dfrac{1}{6}$$",
            "B) $$\\dfrac{1}{3}$$",
            "C) $$\\dfrac{2}{3}$$",
            "D) $$\\dfrac{1}{2}$$",
        ],
        "Why_answer_this_one": "หน้าที่มากกว่า 4 คือ 5, 6 มี 2 หน้า จาก 6 หน้า $$\\dfrac{2}{6} = \\dfrac{1}{3}$$ ตอบข้อ B",
        "correct_answer": "B",
    },
    {
        "question": "หยิบไพ่ 1 ใบจากสำรับไพ่ 52 ใบ ความน่าจะเป็นที่จะได้ไพ่โพแดง (Heart) คือข้อใด?",
        "options": [
            "A) $$\\dfrac{1}{13}$$",
            "B) $$\\dfrac{1}{4}$$",
            "C) $$\\dfrac{1}{26}$$",
            "D) $$\\dfrac{4}{13}$$",
        ],
        "Why_answer_this_one": "โพแดงมี 13 ใบ จาก 52 ใบ ความน่าจะเป็น $$\\dfrac{13}{52} = \\dfrac{1}{4}$$ ตอบข้อ B",
        "correct_answer": "B",
    },
    {
        "question": "โยนเหรียญ 2 เหรียญพร้อมกัน ความน่าจะเป็นที่เหรียญทั้งสองออกหน้าเดียวกันคือเท่าใด?",
        "options": [
            "A) $$\\dfrac{1}{2}$$",
            "B) $$\\dfrac{1}{4}$$",
            "C) $$\\dfrac{2}{3}$$",
            "D) $$\\dfrac{3}{4}$$",
        ],
        "Why_answer_this_one": "กรณีที่หน้าเดียวกันคือ HH, TT มี 2 วิธี จาก 4 วิธี (HH, HT, TH, TT) $$\\dfrac{2}{4} = \\dfrac{1}{2}$$ ตอบข้อ A",
        "correct_answer": "A",
    },
    {
        "question": "ถ้าจำนวนสมาชิกของเหตุการณ์ $$A$$ คือ $$4$$ และผลลัพธ์ทั้งหมดคือ $$10$$ ความน่าจะเป็นของเหตุการณ์ $$A$$ คือข้อใด?",
        "options": [
            "A) $$\\dfrac{1}{2}$$",
            "B) $$\\dfrac{2}{5}$$",
            "C) $$\\dfrac{3}{5}$$",
            "D) $$\\dfrac{4}{5}$$",
        ],
        "Why_answer_this_one": "ความน่าจะเป็นคือ $$\\dfrac{n(A)}{n(S)} = \\dfrac{4}{10} = \\dfrac{2}{5}$$ ตอบข้อ B",
        "correct_answer": "B",
    },
    {
        "question": "สุ่มหยิบลูกแก้วจากถุงที่มีลูกแก้ว 5 สี อย่างละ 1 ลูก ความน่าจะเป็นที่จะหยิบได้สีเขียวเท่ากับข้อใด?",
        "options": [
            "A) $$\\dfrac{1}{5}$$",
            "B) $$\\dfrac{1}{4}$$",
            "C) $$\\dfrac{1}{3}$$",
            "D) $$\\dfrac{1}{2}$$",
        ],
        "Why_answer_this_one": "ลูกแก้ว 5 ลูกสูบได้สีเขียวลูกเดียว $$\\dfrac{1}{5}$$ ตอบข้อ A",
        "correct_answer": "A",
    },
    {
        "question": "ถ้าโยนเหรียญ $$3$$ เหรียญพร้อมกัน ความน่าจะเป็นที่จะได้เหรียญขึ้นหน้าหัว $$2$$ เหรียญคือเท่าใด?",
        "options": [
            "A) $$\\dfrac{1}{8}$$",
            "B) $$\\dfrac{3}{8}$$",
            "C) $$\\dfrac{1}{4}$$",
            "D) $$\\dfrac{1}{2}$$",
        ],
        "Why_answer_this_one": "โยนเหรียญ 3 เหรียญมี 8 ผลลัพธ์ โอกาสที่จะหัว 2 เหรียญมี 3 วิธี (HTH, HHT, THH) ดังนั้น $$\\dfrac{3}{8}$$ ตอบข้อ B",
        "correct_answer": "B",
    },
    {
        "question": "เลือกตัวเลข 1 ตัวจาก $$1$$ ถึง $$10$$ ความน่าจะเป็นที่เลือกได้เลขคู่คือเท่าไหร่?",
        "options": [
            "A) $$\\dfrac{1}{5}$$",
            "B) $$\\dfrac{3}{10}$$",
            "C) $$\\dfrac{1}{2}$$",
            "D) $$\\dfrac{2}{5}$$",
        ],
        "Why_answer_this_one": "เลขคู่มี 2, 4, 6, 8, 10 รวม 5 ตัวจาก 10 ตัว $$\\dfrac{5}{10} = \\dfrac{1}{2}$$ ตอบข้อ C",
        "correct_answer": "C",
    },
    {
        "question": "ถ้าสุ่มหยิบลูกบอล $$2$$ ลูกต่อเนื่องโดยไม่ใส่คืนจากกล่องที่มีลูกบอล $$3$$ สีแดงกับ $$2$$ สีน้ำเงิน ความน่าจะเป็นที่หยิบได้ลูกบอลสีแดงทั้ง $$2$$ ลูกคือข้อใด?",
        "options": [
            "A) $$\\dfrac{3}{10}$$",
            "B) $$\\dfrac{1}{5}$$",
            "C) $$\\dfrac{6}{20}$$",
            "D) $$\\dfrac{3}{5}$$",
        ],
        "Why_answer_this_one": "หยิบบอล 2 ลูกไม่คืน ความน่าจะเป็นดึงแดงลูกแรก $$\\dfrac{3}{5}$$ ลูกสองเหลือ $$2/4$$ คูณกัน $$\\dfrac{3}{5}\\times\\dfrac{2}{4} = \\dfrac{6}{20} = \\dfrac{3}{10}$$ ตอบข้อ A",
        "correct_answer": "A",
    },
]

# -----------------------------
# Router Definition
# -----------------------------
router = APIRouter(prefix="/mock", tags=["mock_exam"])


# 1) Submit route -----------------------------------------------------------
@router.post("/submit", response_model=Ai_ExamResult)
async def submit(payload: ExamSubmissionCreate):
    if len(payload.answers) != len(EXAM_DATA):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of responses does not match number of exam questions.",
        )

    score = 0
    details: List[Dict[str, Any]] = []
    # Map answers by question_id for quick lookup
    answer_map = {ans.question_id: ans.answer for ans in payload.answers}

    for idx, q in enumerate(EXAM_DATA, start=1):
        correct = q["correct_answer"]
        user_ans = answer_map.get(str(idx))
        is_correct = (user_ans or "").upper() == correct.upper()
        if is_correct:
            score += 1
        details.append(
            {
                "question_id": str(idx),
                "user_answer": user_ans,
                "correct_answer": correct,
                "is_correct": is_correct,
            }
        )

    return Ai_ExamResult(score=score, total=len(EXAM_DATA), details=details)


# 2) Get Why-Answer route ----------------------------------------------------
@router.get("/get-why-answer-this-one")
async def get_why_answer_this_one(question_id: int = Query(..., ge=1, le=len(EXAM_DATA), description="Question number (1-indexed)")):
    """Return explanation for a specific question by its number."""
    index = question_id - 1
    if index < 0 or index >= len(EXAM_DATA):
        raise HTTPException(status_code=404, detail="Question not found")
    q = EXAM_DATA[index]
    return {
        "question_id": question_id,
        "question": q["question"],
        "why": q["Why_answer_this_one"],
    }


# 3) Get Exam route ----------------------------------------------------------
@router.get("/get-exam", response_model=List[ExamQuestion])
async def get_exam():
    """Return exam questions without revealing answers."""
    return [
        ExamQuestion(
            id=str(idx + 1),
            type="multiple_choice",
            question=q["question"],
            choices=q["options"],
            answer=None,  # hide correct answer
        )
        for idx, q in enumerate(EXAM_DATA)
    ]


# 4) Analysis route ----------------------------------------------------------
@router.get("/analysis")
async def analysis():
    """Return the full dataset including answers and explanations."""
    return EXAM_DATA

# 5) Exam file route ---------------------------------------------------------
@router.get("/exam-file", response_model=ExamFileOut)
async def get_exam_file():
    """Return static ExamFileOut pointing to hosted PDF."""
    return ExamFileOut(
        id="static-1",
        title="ข้อสอบเรื่องความน่าจะเป็น",
        description="ความน่าจถเป็น",
        tags=["possiblity", "math", "exam"],
        url="https://cdn.regenxyy.me/student_exam.pdf",
        uploaded_by="admin@admin.com",
        essay_count=0,
        choice_count=10,
    )
