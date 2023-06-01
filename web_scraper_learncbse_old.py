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
         "Problems Based on Conversion of Solids",
         "Very Short Answer Questions(VSA) 1 Mark",
         "Short Answer Questions (SA) 3 Marks",
         "Long Answer Questions 5 Marks"
        ]
question_lists = {}
child_texts = []
sst_links_list = {}

config = json.load(open("./config.json", "r"))
db_client = motor.motor_asyncio.AsyncIOMotorClient(config["MONGO_DB_URL"])
db = db_client["TopperHQ"]


async def get_sst_links(url: str = "https://www.learncbse.in/social-science-class-10-important-questions/"):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            soup = BeautifulSoup(await response.text(), 'html.parser')
            footer_section = soup.find_all(["h3", "ol"])
            for element in footer_section:
                if element.name == "h3":
                    sst_links_list[element.text.replace("Social Science Class 10 Important Questions", "").strip()] = []
                if element.name == "ol":
                    for li in element.find_all("li"):
                        a_element = li.find("a")
                        href = a_element["href"]
                        title = a_element["title"]
                        match = re.search(r'Chapter \d+ (.+?)(?: Class|$)', title)
                        new_title = match.group(1)
                        if "Economics" in title:
                            sst_links_list["Economics"].append({new_title: href})
                        if "Geography" in title:
                            sst_links_list["Geography"].append({new_title: href})
                        if "History" in title:
                            sst_links_list["History"].append({new_title: href})
                        if "Political Science" in title:
                            sst_links_list["Political Science"].append({new_title: href})
            
            return sst_links_list
    

async def get_qna_learncbse(links_list: dict):
    
    for subject, links_list_ in links_list.items():
        for obj in links_list_:
            for title, link in obj.items():
                await asyncio.sleep(1)
                async with aiohttp.ClientSession() as session:
                    async with session.get(link) as response:
                        soup = BeautifulSoup(await response.text(), 'html.parser')
                        content_div = soup.find("div", class_="entry-content")
                        for element in content_div:
                            current_type = ""
                            question_text = ""
                            answer_text = ""
                            if element.name == "h3":
                                pass
                            if element.name == "p":
                                
                                if element.text in types:
                                    current_type = element.text
                                    question_lists[element.text] = []

                                if current_type is not None:
                                    if not element.text.strip().lower().startswith("question") or not element.text.strip().lower().startswith("answer"):
                                        answer_text += "\n" + element.text.strip()
                                    
                                    if element.find("br") is not None:
                                        
                                        items = element.get_text(separator="<br>").split("<br>")
                                        for item in items:
                                            if item.strip().lower().startswith("question"):
                                                question_index = items.index(item)
                                                for item in items:
                                                    if item.strip().lower().startswith("answer"):
                                                        break
                                                    if not item.strip().lower().startswith("question"):
                                                        question_text += "\n" + item.strip()
                                                    
                                                
                                            if item.strip().lower().startswith("answer"):
                                                answer_index = items.index(item)
                                                for item in items:
                                                    if item.strip().lower().startswith("question"):
                                                        break
                                                    if not item.strip().lower().startswith("answer"):
                                                        answer_text += "\n" + item.strip()
                            
                                                    
                                                
                                            else:
                                                pass
                                        pass
                                    
                                    
                                if current_type is not None and element.name == "ol":
                                    current = 1
                                    for i in element.children:
                                        answer_text += f"\n {current}" + i.text
                                        current += 1
                                
                                if current_type is not None and element.name == "ul":
                                    for i in element.children:
                                        answer_text += "\n• " + i.text
                                    
                            print("question text: \n" + question_text, "answer text: \n" + answer_text)
                    

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_qna_learncbse({'History': [{'The Rise of Nationalism in Europe': 'https://www.learncbse.in/social-science-class-10-important-questions-history-chapter-1/'}]}))