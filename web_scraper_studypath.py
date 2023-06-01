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
         "Long Answer (4 Marks)",
         "Long Answer Type Questions",
         "Short Answer Type Questions",
         "Very Short Answer Questions"
        ]
question_lists = {}
child_texts = []
english_first_flights_links_list = []

config = json.load(open("./config.json", "r"))
db_client = motor.motor_asyncio.AsyncIOMotorClient(config["MONGO_DB_URL"])
db = db_client["TopperHQ"]


async def get_english_links(url: str = "https://www.thestudypath.com/class-10/extra-questions/english/first-flight/"):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            soup = BeautifulSoup(await response.text(), 'html.parser')
            entry_content = soup.find("div", class_="entry-content")
            english_first_flights_links_list = {"Prose": [], "Poems": []}
            for element in entry_content:
                if element.name == "ol":
                    for li in element.children:
                        a_element = li.find("a")
                        href = a_element["href"]
                        title = a_element.text
                        
                        new_title = title.split("–")[1].strip()
                        if "Chapter" in title:
                            english_first_flights_links_list["Prose"].append({new_title: href})
                        if "Poem" in title:
                            english_first_flights_links_list["Poems"].append({new_title: href})
                        

            print(english_first_flights_links_list)
            return english_first_flights_links_list

    
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

    question_indexes = [index for index, item in enumerate(data) if re.match(r"^\d", item)]
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


async def get_qna_studypath(links_list: dict):
    for subject, links_list_ in links_list.items():
        for obj in links_list_:
            for title, link in obj.items():
                await asyncio.sleep(1)
                async with aiohttp.ClientSession() as session:
                    async with session.get(link) as response:
                        soup = BeautifulSoup(await response.text(), 'html.parser')
                        content_div = soup.find("div", class_="entry-content")
                        headings = content_div.find_all("h3")
                        content_div = content_div.find_all(["h3", "p"])[1:]
                        new_content_div = []
                        formatted_data = {}
                        for element in content_div:
                            text = re.sub(r'\s+|&nbsp;', ' ', element.text.strip())
                            
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
                                new_content_div.append(text)
                        new_content_div_ = []
                        for item in new_content_div:
                            if "Extract Based Questions" in item:
                                break
                            if "Self- Assessment Test" in item:
                                break
                            if item in types:
                                pass
                            if "Part 2" in item or "Part 1" in item:
                                continue
                            else:
                                new_content_div_.append(item)

                        new_content_div__ = []
                        
                        for item in new_content_div_:
                            parts = item.split('\n')
                            for part in parts:
                                split_parts = part.split('Answer:')
                                for i, split_part in enumerate(split_parts):
                                    stripped_part = split_part.strip()
                                    if stripped_part:
                                        if i == 0:
                                            new_content_div__.append(stripped_part)
                                        else:
                                            new_content_div__.append(f"Answer: {stripped_part}")
                        
                        all = [x.strip() for x in new_content_div__ if (x != "")]
                        all = [x.strip() for x in new_content_div__ if (x!= "\n")]

                        results = []
                        question_indexes = [index for index, item in enumerate(all) if item.lower().startswith("question")]
                        answer_indexes = [index for index, item in enumerate(all) if item.lower().startswith('answer')]
                        print(question_indexes)
                        print(answer_indexes)
                        decimal_starting_pattern = r'Question \d+:'
                        for i, question_index in enumerate(question_indexes):
                            
                            if question_index == question_indexes[i] and question_index != question_indexes[-1]:
                                try:
                                    question_text = re.sub(decimal_starting_pattern, '', '\n'.join(all[question_indexes[i]:answer_indexes[i]])).strip() if re.sub(decimal_starting_pattern, '', '\n'.join(all[question_indexes[i]:answer_indexes[i]])) != "" else re.sub(decimal_starting_pattern, '', all[question_indexes[i]]).strip()
                                    if i + 1 < len(question_indexes):
                                        answer_text = '\n'.join(all[answer_indexes[i-2]:question_indexes[i]]).replace("Answer:", "").strip()
                                    else:
                                        answer_text = '\n'.join(all[answer_indexes[i-2]:]).replace("Answer:", "").strip()
                                    results.append({'question_text': question_text, 'answer_text': answer_text})
                                except Exception as e:
                                    continue
                            
                            if question_index == question_indexes[-1]:
                                question_text = re.sub(decimal_starting_pattern, '','\n'.join(all[question_indexes[-1] :answer_indexes[-1]])).strip()
                                answer_text = '\n'.join(all[answer_indexes[-1]:]).replace("Answer:", "").strip()
                                results.append({'question_text': question_text, 'answer_text': answer_text})

                        print(results)
                        # await add_to_database(subject=subject, chapter=title, data=results)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_qna_studypath({'English First Flight Poems': [{'The Trees': 'https://www.thestudypath.com/class-10/extra-questions/english/first-flight/poem-8-the-trees/'}]}))
