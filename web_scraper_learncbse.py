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
         "Long Answer Questions 5 Marks",
         "Short Answer Question3 Marks",
         "Long Answer Questions (LA) 5 Marks",
         "Short Answer-I (2 Marks)",
         "Very Short Answer (1 Mark)",
         "Short Answer-II (3 Marks)",
         "Long Answer (4 Marks)"
        ]
question_lists = {}
child_texts = []
sst_links_list = {}
maths_links_list = []

config = json.load(open("./config.json", "r"))
db_client = motor.motor_asyncio.AsyncIOMotorClient(config["MONGO_DB_URL"])
db = db_client["TopperHQ"]


async def get_maths_links(url: str = "https://www.learncbse.in/important-questions-for-class-10-maths/"):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            soup = BeautifulSoup(await response.text(), 'html.parser')
            footer_section = soup.find_all(["h3", "ol"])
            for element in footer_section:
                if element.name == "ol":
                    for li in element.find_all("li"):
                        a_element = li.find("a")
                        href = a_element["href"]
                        title = a_element["title"]
                        pattern = r'Chapter \d+ (.*)'
                        maths_links_list.append({re.search(pattern, title).group(1): href})
            print(maths_links_list)
            return maths_links_list


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
    
    
def remove_duplicate_dicts(lst):
    return list({frozenset((k, tuple(v)) for k, v in d.items()): d for d in lst}.values())


def convert_to_dicts(elements, indexes):
    result = []

    for i in range(len(indexes)):
        start_index = indexes[i]
        end_index = indexes[i + 1] - 1 if i < len(indexes) - 1 else len(elements) - 1
        element_range = [elem for elem in elements[start_index+1:end_index + 1] if elem != "\n"]
        
        if element_range:
            element_dict = {elements[start_index]: element_range}
            result.append(element_dict)

    if indexes[-1] != len(elements) - 1:
        last_index = len(elements) - 1
        last_range = [elem for elem in elements[indexes[-1]+1:last_index + 1] if elem != "\n"]
        
        if last_range:
            last_dict = {elements[indexes[-1]]: last_range}
            result.append(last_dict)

    return remove_duplicate_dicts(result)


def filter_similar_strings(data):
    result = []
    seen = set()

    for item in data:
        key = item.split(" ")[0]
        if key in seen:
            continue
        similar_items = [x for x in data if x.startswith(key)]
        if len(similar_items) > 1:
            longest_item = max(similar_items, key=len)
            result.append(longest_item)
        else:
            result.append(item)
        seen.add(key)

    return result

def split_data(data):
    question_indexes = [index for index, item in enumerate(data) if item.lower().startswith('question')]
    answer_indexes = [index for index, item in enumerate(data) if item.lower().startswith('answer')]
    print(question_indexes, answer_indexes)
    questions = []
    for question_index, answer_index in zip(question_indexes, answer_indexes):
        question_text = "".join(data[question_index + 1:answer_index])
        answer_text = "".join(data[answer_index + 1:question_index])
        questions.append({"question_text": question_text, "answer_text": answer_text})

    return questions

async def add_to_database(subject: str, chapter: str, data: list):
    await db[subject].insert_one({chapter: data})
    print(f"Successfully inserted {chapter} ({subject}).")

async def get_qna_learncbse(links_list: dict):
    for subject, links_list_ in links_list.items():
        for obj in links_list_:
            for title, link in obj.items():
                await asyncio.sleep(1)
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(link) as response:
                        soup = BeautifulSoup(await response.text(), 'html.parser')
                        content_div = soup.find("div", class_="entry-content")
                        
                        new_content_div = []
                        formatted_data = {}
                        for element in content_div:
                            if element.text == "\n":
                                pass
                            if element.name == "ol":
                                current = 1
                                for li in element.children:
                                    if li.name == "p":
                                        new_content_div.append(li)
                                    if li.name == "li":
                                        new_content_div.append(str(current) + " " + li.text)
                                        current+=1
                            if element.name == "ul":
                                for li in element.children:
                                    if li.name == "p":
                                        new_content_div.append(li)
                                    if li.name == "li":
                                        new_content_div.append("• " + li.text)
                            
                            else:
                                new_content_div.append(element.text)
                        print(new_content_div)
                        qna_headings_indexes = []
                        for element in new_content_div:
                            for type in types:
                                if type in element:
                                    qna_headings_indexes.append(new_content_div.index(element))
                            
                        sub_lists = convert_to_dicts(list(new_content_div), qna_headings_indexes)
                        questions = []
                        questions_index = []
                        answers = []
                        answers_index = []
                        new_all = new_content_div
                        all = []
                        for category in sub_lists:
                            for question_type, question_list in category.items():
                                formatted_data.setdefault(question_type, [])
                                sum_list = sum((string.split("\n") for string in question_list), [])
                                all.extend(sum_list)
                        
                        all = [x.strip() for x in all if (x != "")]
                        all = [x.strip() for x in all if (x!= "\n")]
                        
                        results = []
                        question_indexes = [index for index, item in enumerate(all) if item.lower().startswith('question')]
                        answer_indexes = [index for index, item in enumerate(all) if item.lower().startswith('solution')]
                        print(question_indexes)
                        print(answer_indexes)
                        
                        for i, question_index in enumerate(question_indexes):
                            
                            if question_index == question_indexes[i]:
                                try:
                                    question_text = '\n'.join(all[question_indexes[i] + 1:answer_indexes[i]])
                                    if i + 1 < len(question_indexes):
                                        answer_text = '\n'.join(all[answer_indexes[i]+1:question_indexes[i+1]])
                                    else:
                                        answer_text = '\n'.join(all[answer_indexes[i]+1:])
                                    results.append({'question_text': question_text, 'answer_text': answer_text})
                                except Exception as e:
                                    continue

                            if question_index == question_indexes[-1]:
                                question_text = '\n'.join(all[question_indexes[-1] + 1:answer_indexes[-1]])
                                answer_text = '\n'.join(all[answer_indexes[-1] + 1:])
                                results.append({'question_text': question_text, 'answer_text': answer_text})

                        print(results)
                        await add_to_database(subject=subject, chapter=title, data=results)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_qna_learncbse({'Maths': [{'Real Numbers': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-1/'}, {'Polynomials': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-2/'}, {'Pair of Linear Equations in Two Variables': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-3/'}, {'Quadratic Equations': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-4/'}, {'Arithmetic Progressions': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-5/'}, {'Triangles': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-6/'}, {'Coordinate Geometry': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-7/'}, {'Introduction to Trigonometry': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-8/'}, {'Some Applications of Trigonometry': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-9/'}, {'Circles': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-10/'}, {'Constructions': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-11/'}, {'Areas Related to Circles': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-12/'}, {'Surface Areas and Volumes': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-13/'}, {'Statistics': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-14/'}, {'Probability': 'https://www.learncbse.in/important-questions-for-class-10-maths-chapter-15/'}]}))
