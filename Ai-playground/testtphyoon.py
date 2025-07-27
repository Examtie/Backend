import requests
import json, re

url = "https://api.opentyphoon.ai/v1/chat/completions"

payload = {
  "model": "typhoon-v2.1-12b-instruct",
  "messages": [
    {
      "role": "system",
      "content": '''
# ROLE:
Act as an expert multiple-choice question generator for educational purposes.

# PROMPT:
You are provided with a context. Based on the context, generate 5 multiple-choice questions. Each question should have 4 answer options, with only one correct answer. Structure your response in JSON format.

# CONTEXT:
[Context]

# INSTRUCTIONS:

- Generate **exactly 30 questions** based on the provided context.
- Each question must have **4 answer options** labeled **A, B, C, D**, with one or multiple correct answers.
- Ensure the questions comprehensively cover the key details from the context.
- **Do not repeat** questions or options across the generated set.
- Provide the correct answer as a ** letter (A, B, C, or D)** in the `correct_answer` field.
- Follow the specific JSON format provided below. No extra text or explanations.
- **Language** in Exam Question and Choice Depends On Context Language
- Math Question Use **LaTeX** for **Math Equation** Or **Any Equation** Use **LaTeX** Instead Of Normal English and Number
- An Advance Question and Interesting Equation Use Skill to Solve But still in provided Context


# IMPORTANT:
- **Language** in Exam Question and Choice Depends On Context Language
- For MATH Equations Use **LaTeX** for **Math Equation** Or **Any Equation** Use **LaTeX** Instead Of Normal English and Number


# JSON FORMAT:
[
    {
        "question": "Question text here",
        "options": [
            "A) Option text",
            "B) Option text",
            "C) Option text",
            "D) Option text"
        ],
        "correct_answer": "A"
    },
    {
        "question": "Question text here",
        "options": [
            "A) Option text",
            "B) Option text",
            "C) Option text",
            "D) Option text"
        ],
        "correct_answer": "B, D"
    },
]
'''
    },
    {
      "role": "user",
      "content": '''
สาระด้าน จ านวนและพีชคณิต
1) จ านวนจริง
จ านวนจริงและสมบัติของจ านวนจริง
ค่าสัมบูรณ์ของจ านวนจริงและสมบัติของค่าสัมบูรณ์ของจ านวนจริง
จ านวนจริงในรูปกรณฑ์ และจ านวนจริง ในรูปเลขยกก าลัง
จ านวนตรรกยะ และจ านวนอตรรกยะ รากที่สองและรากที่สามของจ านวนตรรกยะ
เศษส่วน และ สัดส่วน (Fractions, percentages)
2) ทฤษฎีจ ำนวนเบื้องต้น
การหารจ านวนเต็ม (ขั้นตอนวิธีการหาร) การหารลงตัว และเศษเหลือการหาร
จ านวนเฉพาะ จ านวนประกอบ คุณสมบัติของจ านวนเฉพาะ
เลขคณิตมอดุลาร์ (Modular Arithmetic) : การบวก การลบ การคูณ
3) ความสัมพันธ์ ฟังก์ชัน
พหุนาม : การบวก การลบ การคูณ และการหารพหุนาม
ตัวประกอบพหุนาม การแยกตัวประกอบของพหุนาม
ความสัมพันธ์ ฟังก์ชัน และกราฟของฟังก์ชันก าลังสอง
คุณสมบัติของความสัมพันธ์ : สะท้อน สมมาตร ถ่ายทอด เทียบเท่าหรือสมมูล
ประเภทของฟังก์ชัน (การบวก การลบ การคูณ การหารฟังก์ชัน ฟังก์ชันประกอบ ฟังก์ชันผกผัน)
ฟังก์ชันเอกซ์โพเนนเชียล และฟังก์ชันลอการิทึม และกราฟของฟังก์ชัน
4) สมการ และ อสมการ
อสมการเชิงเส้นตัวแปรเดียว การแก้อสมการเชิงเส้นตัวแปรเดียว
สมการก าลังสองตัวแปรเดียว การแก้สมการก าลังสองตัวแปรเดียว
ระบบสมการเชิงเส้นสองตัวแปร การแก้ระบบสมการเชิงเส้นสองตัวแปร
สมการและอสมการ (พหุนามตัวแปรเดียวดีกรีไม่เกินสี่ )

'''
    }
  ],
  "temperature": 0.6,
  "top_p": 0.95,
  "repetition_penalty": 1.05,
  "stream": False
}

headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer sk-'
}

response = requests.request("POST", url, headers=headers, json=payload)

print(response.json())
response_obj = response.json()

# ✅ Step 1: Extract the content string
content_str = response_obj['choices'][0]['message']['content']

# ✅ Step 2: Extract the JSON block inside triple backticks
match = re.search(r'```json(.*?)```', content_str, re.DOTALL)
if match:
    json_str = match.group(1).strip()

    # ✅ Step 3: Escape backslashes so it's valid JSON
    json_str = json_str.replace('\\', '\\\\')

    # ✅ Step 4: Parse JSON
    try:
        questions = json.loads(json_str)
        print(questions)
    except json.JSONDecodeError as e:
        print("JSON decoding error:", e)
else:
    print("JSON block not found.")