import requests
import json, re
from json_repair import repair_json
from openai import AzureOpenAI


class Azzzure_API:
    def __init__(self, api_key: str, azure_endpoint: str, api_version: str, Azure_Model: str):
        self.client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=azure_endpoint,
            api_key=api_key
        )
        self.model = Azure_Model
        self.pdf_to_exam_system = """
- If You are useing LaTex You need to cover Latex in $ Front and the End Of the Equations
# ROLE:
Act as an expert multiple-choice question generator for educational purposes.

# PROMPT:
You are provided with a context. Based on the context, generate 5 multiple-choice questions. Each question should have 4 answer options, with only one correct answer. Structure your response in JSON format. Cover latex equation in $...$ (for example, $x=e^2$)

# CONTEXT:
[Context]

# INSTRUCTIONS:
- If You are useing LaTex You need to cover Latex in $ Front and the End Of the Equations
- Each question must have **4 answer options** labeled **A, B, C, D**, with **one correct** answers.
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
- If You are useing LaTex You need to cover Latex in $ Front and the End Of the Equations
- Explain how to solve the question or equation in field `why_answer_this_one`
- Explain If i want to Do this Question or Equation in `what_do_i_read`  what do i need to read more or do more practice

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
        "why_answer_this_one": "Explanation here",
        "what_do_i_read": "Explanation here",
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
        "why_answer_this_one": "Explanation here",
        "what_do_i_read": "Explanation here",
        "correct_answer": "B"
    },
]
        """

        self.flashcard_from_prompt = """
# ROLE 
YOU CAN USE ANY LANGUAGE NOT ONLY ENGLISH

You are an advanced flashcard creator specializing in graduate and post-graduate level content. high-quality flashcards on the given topic. Follow these guidelines:

# INSTRUCTIONS:
  1. Check the context language and create flashcards in that language.
  2. Questions should be challenging and in-depth, suitable for graduate or post-graduate level study.
  3. Avoid basic definitions or questions that can be answered with a single word from the topic itself.
  4. Answers MUST BE CONCISE, but may contain multiple words or a short phrase when necessary for accuracy. Answers MUST NOT BE MORE THAN 5 WORDS LONG.
  5. Ensure all answers are unique with no repetitions.
  6. Cover a diverse range of subtopics within the main topic to provide comprehensive coverage.
  7. Include questions that test understanding of concepts, theories, applications, and critical thinking.
  8. Avoid questions that can be answered with a simple "yes" or "no".
  9. Complete All the flashcards in the JSON format provided below.
  
# IMPORTANT
    - **Language** in Flashcard Question and Answer Depends On Context Language in FRONT AND BACK OF THE FLASHCARD THE WHOLE FLASHCARD DEPENDS ON CONTEXT LANGUAGE
    - For MATH Equations Use **LaTeX** for **Math Equation** Or **Any Equation** Use **LaTeX** Instead Of Normal English Letters and Number. To use LaTeX cover the equation with $...$

# CONTEXT:
[Context]

# JSON FORMAT:

  Return the flashcards in the following JSON format:

  {
    "flashcards": [
      {
        "front": "Detailed, challenging question related to the topic",
        "back": "Concise, accurate answer (can be a short phrase if needed)"
      }
    ]
  }

Example topic: "Fundamentals of Psychology"
Instead of "Which branch studies the human mind?", ask something like:
"What cognitive bias describes the tendency to search for or interpret information in a way that confirms one's preexisting beliefs?"
Answer: "Confirmation bias"
"""


    def ai_azure(self, prompt: str, system_prompt: str) -> str:
        print(system_prompt)
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )

        message = completion.choices[0].message.content
        if message.startswith("```json"):
            message = message.split("```json")[-1]
            message = message.rsplit("```", 1)[0].strip()

        try:
            fixed_json_str = repair_json(message)
            exam_data = json.loads(fixed_json_str)
            return exam_data
        except json.decoder.JSONDecodeError as e:
            print("JSON decoding error:", e)
            return False
    
    def generate_exam_questions(self, context: str, amount: int = 10) -> str:
        print("you changede")
        #prompt = f"สร้างข้อสอบจำนวน  {amount} ข้อ และข้อสอบเนื้อหาเกี่ยวกับ : {context}"
        return self.ai_azure(f"สร้างข้อสอบจำนวน  {amount} ข้อ และข้อสอบเนื้อหาเกี่ยวกับ : {context}", self.pdf_to_exam_system)
    
    def generate_flashcards(self, context: str, amount: int = 10) -> str:
        #message = self.ai_azure(f"สร้างแฟรการ์ด เกี่ยวกับ {topic} มัธยมศึกษาปีที่ 5 \nจำนวน {amount} แฟรชการ์ด.", self.flashcard_from_prompt)
        return self.ai_azure(f"สร้างแฟรการ์ด เกี่ยวกับ {context} มัธยมศึกษาปีที่ 5 \nจำนวน {amount} แฟรชการ์ด.", self.flashcard_from_prompt)
