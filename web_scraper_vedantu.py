import aiohttp, asyncio
from bs4 import BeautifulSoup
import re
import motor.motor_asyncio
import json

types = ["Very Short Answer Questions (1 Mark)",
         "1 Mark Questions",
         "Level - 01 (01 Marks)",
         "Level 2 (02 Marks)",
         "Level 3 (03 Marks)",
         "1 Mark Question",
         "1 Marks Questions",
         "2 Marks Questions",
         "3 Marks Questions",
         "4 Marks Questions",
         "Short Answer Questions (2 Marks)",
         "2 Marks Questions",
         "Short Answer Questions (3 Marks)",
         "3 Marks Questions",
         "Long Answer Questions (4 Marks)",
         "Long Answer Questions (5 Marks)",
         "5 Marks Questions",
         "Problems Based on Conversion of Solids"
        ]
question_lists = {}
child_texts = []

config = json.load(open("./config.json", "r"))
db_client = motor.motor_asyncio.AsyncIOMotorClient(config["MONGO_DB_URL"])
db = db_client["TopperHQ"]


async def get_questions_answers_vedantu(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            soup = BeautifulSoup(await response.text(), 'html.parser')
            footer_section = soup.find('div', id='footerDescription')
            current_type = None
            for child in footer_section.contents[0].find_all(["p", "h2", "h3"]):
                child_text = re.sub(r'\s+|&nbsp;', ' ', child.text.strip())
                # if "important questions" in child.text.lower()  or "ncert solutions" in child.text.lower() or "download free pdf" in child.text.lower() or "conclusion" in child.text.lower():
                if "CBSE Class 10 Maths Probability Important Questions" in child.text:
                # if "Important Questions and Solutions Summary" in child.text or "Chapter 11 Science Class 10 Important Questions" in child.text:
                    break
                if child_text is not None and child_text in types:
                    current_type = child_text
                    question_lists[current_type] = []
                elif current_type is not None:
                    question_lists[current_type].append(child_text)
            for question_type, questions in question_lists.items():
                question_lists[question_type] = []
                question_text = None
                ans_text = ""
                subpart_questions = []
                question_index = 0
                answer_index = 0
                for question in questions:
                    print(question)
                    if re.match(r'^\d+\.', question):
                        question_index = questions.index(question)
                        if question_text is not None:
                            if ans_text:
                                question_dict = {
                                    "question_text": question_text.strip(),
                                    "ans_text": ans_text.strip()
                                }
                                question_lists[question_type].append(question_dict)
                                for subpart_question in subpart_questions:
                                    question_lists[question_type].append(subpart_question)
                            else:
                                try:
                                    question_lists[question_type][-1]["question_text"] += " " + question_text.strip()
                                except: pass
                        question_text = re.sub(r'^\d+\.\s*', '', question)
                        ans_text = ""
                        subpart_questions = []
                        
                    elif question.startswith("Ans:"):
                        answer_index = questions.index(question)
                        if ans_text:  # If ans_text already contains content, include it in the question_text
                            ans_text += " " + ans_text
                        ans_text = re.sub(r'^Ans:\s*', '', question)
                        
                    elif re.match(r'^[a-zA-Z0-9]+[.)]', question):
                        if question_text is not None:
                            if subpart_questions:
                                question_dict = {
                                    "question_text": subpart_questions[0]["question_text"],
                                    "ans_text": ans_text.strip()
                                }
                                question_lists[question_type].append(question_dict)
                                for subpart_question in subpart_questions[1:]:
                                    question_lists[question_type].append(subpart_question)
                            else:
                                try:
                                    question_lists[question_type][-1]["question_text"] += " " + question_text.strip()
                                except:
                                    pass

                            subpart_questions = [{
                                "question_text": f"{question_text} {question}",
                                "ans_text": ""
                            }]
                    
                    if question_text and questions.index(question) > question_index:
                            if not question.lower().startswith("ans:"):
                                question_text += "\n" + question
                    if ans_text and questions.index(question) > answer_index:
                        ans_text += "\n" + question
                
                    elif question_text is not None:
                        pass

                if question_text:
                    if ans_text:
                        question_dict = {
                            "question_text": question_text.strip(),
                            "ans_text": ans_text.strip()
                        }
                        question_lists[question_type].append(question_dict)
                        for subpart_question in subpart_questions:
                            question_lists[question_type].append(subpart_question)
            
            for question_type, questions in question_lists.items():
                question_lists[question_type] = [question for question in questions if question["ans_text"]]
            
            print(question_lists)
            return question_lists
        
chapters_urls = {
    "Probability": "https://www.vedantu.com/cbse/important-questions-class-10-maths-chapter-15"
}

async def add_to_database(chapters_urls: dict):
    for k, v in chapters_urls.items():
        data = await get_questions_answers_vedantu(url=v)
        result = await db["Maths"].insert_one({k: data})
    
    print(f"Successfully inserted {len(chapters_urls)} documents.")
    

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_questions_answers_vedantu(chapters_urls["Probability"]))