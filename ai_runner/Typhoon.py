import requests
import json, re 


class Typhoon_API:
    def __init__(self, api_key: str):
        self.api_url = "https://api.opentyphoon.ai/v1/chat/completions"
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        self.pdf_to_exam_system = """
# ROLE:
Act as an expert multiple-choice question generator for educational purposes.

# PROMPT:
You are provided with a context. Based on the context, generate 5 multiple-choice questions. Each question should have 4 answer options, with only one correct answer. Structure your response in JSON format.

# CONTEXT:
[Context]

# INSTRUCTIONS:
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
        "correct_answer": "B"
    },
]
        """

        self.flashcard_from_prompt = """
# ROLE 
LANGUAGE IN FRONT AND BACK OF THE FLASHCARD DEPENDS ON CONTEXT LANGUAGE
LOOK AT THE CONTEXT LANGUAGE DEPENDS ON THAT NOT ONLY ENGLISH YOU CAN USE ANY LANGUAGE

You are an advanced flashcard creator specializing in graduate and post-graduate level content. high-quality flashcards on the given topic. Follow these guidelines:

# INSTRUCTIONS:
  2. Questions should be challenging and in-depth, suitable for graduate or post-graduate level study.
  3. Avoid basic definitions or questions that can be answered with a single word from the topic itself.
  4. Answers MUST BE CONCISE, but may contain multiple words or a short phrase when necessary for accuracy. Answers MUST NOT BE MORE THAN 5 WORDS LONG.
  5. Ensure all answers are unique with no repetitions.
  6. Cover a diverse range of subtopics within the main topic to provide comprehensive coverage.
  7. Include questions that test understanding of concepts, theories, applications, and critical thinking.
  8. Avoid questions that can be answered with a simple "yes" or "no".
  
# IMPORTANT
    - **Language** in Flashcard Question and Answer Depends On Context Language in FRONT AND BACK OF THE FLASHCARD THE WHOLE FLASHCARD DEPENDS ON CONTEXT LANGUAGE
    - For MATH Equations Use **LaTeX** for **Math Equation** Or **Any Equation** Use **LaTeX** Instead Of Normal English Letters and Number

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

    def json_formatter(self,data: str) -> str:
        math_2 = re.search(r'```json(.*?)```', data, re.DOTALL)
        if math_2:
            json_str = math_2.group(1).strip()
            json_str = json_str.replace('\\', '\\\\')

            try:
                questions = json.loads(json_str)
                return questions
            except json.JSONDecodeError as e:
                print("JSON decoding error:", e)
                return False
        else:
            print("JSON block not found.")
            return False

    def generate_exam_questions(self, context: str, amount: int = 10) -> str:
        payload = {
            "model": "typhoon-v2.1-12b-instruct",
            "messages": [
                {
                    "role": "system",
                    "content": self.pdf_to_exam_system
                },
                {
                    "role": "user",
                    "content": "Context: " + context + "\nCreate exactly " + str(amount) + " Exams."
                }
            ],
            "max_tokens": 8000,
            "temperature": 0.6,
            "top_p": 0.95,
            "repetition_penalty": 1.05,
            "stream": False
        }

        response = requests.post(self.api_url, headers=self.headers, json =payload)

        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            return self.json_formatter(message)
        else:
            raise Exception(f"Question generation failed: {response.status_code} - {response.text}")
    
    def generate_flashcards(self, topic: str, amount: int = 10) -> str:
        print(f"สร้างแฟรการ์ด เกี่ยวกับ {topic}\nจำนวน {amount} แฟรชการ์ด.")
        payload = {
            "model": "typhoon-v2.1-12b-instruct",
            "messages": [
                {
                    "role": "system",
                    "content": self.flashcard_from_prompt
                },
                {
                    "role": "user",
                    "content": f"สร้างแฟรการ์ด เกี่ยวกับ {topic}\nจำนวน {amount} แฟรชการ์ด."
                }
            ],
        }

        response = requests.post(self.api_url, headers=self.headers, data=json.dumps(payload))

        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            return self.json_formatter(message)
        else:
            raise Exception(f"Flashcard generation failed: {response.status_code} - {response.text}")
