from flask import Flask, render_template, redirect, request
import asyncio
import pymongo
from pymongo import MongoClient
import json

import urllib

app = Flask(__name__)
config = json.load(open("./config.json", "r"))
db_client = MongoClient(config["MONGO_DB_URL"])
db = db_client["TopperHQ"]


english_chapter_names = [
    "Fire and Ice",
    "A Tiger in the Zoo",
    "How to Tell Wild Animals",
    "The Ball Poem",
    "Amanda",
    "Fog",
    "Dust of Snow",
    "The Trees",
    "The Tale of Custard the Dragon",
    "For Anne Gregory",
    "Animals",
    "A Letter to God",
    "Nelson Mandela: Long Walk to Freedom",
    "From the Diary of Anne Frank",
    "The Hundred Dresses Part 1",
    "The Hundred Dresses Part 2",
    "Glimpses of India (A Baker from Goa)",
    "Glimpses of India (Coorg)",
    "Glimpses of India (Tea from Assam)",
    "Mijbil the Otter",
    "Madam Rides the Bus",
    "The Sermon at Benares",
    "The Proposal",
    "Two Stories about Flying",
]
maths_chapter_names = [
    "Real Numbers",
    "Polynomials",
    "Quadratic Equations",
    "Arithmetic Progressions",
    "Triangles",
    "Introduction to Trigonometry",
    "Circles",
    "Areas Related to Circles",
    "Surface Areas and Volumes",
    "Statistics"
]
science_chapter_names = [
    "Chemical Reactions and Equations",
    "Acids Bases and Salts",
    "Metals and Non-Metals",
    "Carbon and Its Compounds",
    "Life Processes",
    "Control and Coordination",
    "How do Organisms Reproduce?",
    "Heredity and Evolution",
    "Electricity",
    "Magnetic Effects of Electric Current",
    "Reflection and Refraction of Light",
    "Human Eye and Colourful World",
    "Sources of Energy",
    "Our Environment"
]

def fetch_all_object_names_from_all_collections():
    collection_names = db.list_collection_names()
    object_names = []
    for collection_name in collection_names:
        collection = db[collection_name]
        for document in collection.find({}):
            object_names.extend(document.keys())
    return [x for x in object_names if x != "_id"]
    

def search_objects_by_name(name : str):
    collection_names = db.list_collection_names()
    matching_objects = []
    for collection_name in collection_names:
        collection = db[collection_name]
        for document in collection.find({}):
            for key, value in document.items():
                if key == name:
                    matching_objects.append(value)
    return matching_objects


@app.errorhandler(404)
def page_not_found(e):
    return redirect('/welcome')


@app.route('/welcome')
def welcome():
    return render_template('Landing page.html')


@app.route('/class10')
def class_10():
    return render_template('class10.html')

@app.route('/books')
def class_10_books():
    return render_template('Books.html')

@app.route("/english")
def class_10_english():
    cursor = db["English First Flight Poems"].find({})
    data = []
    for x in cursor:
        data.append(x)
    poems_chapter_names = [list(x)[1] for x in data]
    cursor = db["English First Flight Prose"].find({})
    data = []
    for x in cursor:
        data.append(x)
    prose_chapter_names = [list(x)[1] for x in data]
    return render_template('English.html', subject = "English", poems_chapter_names=poems_chapter_names, prose_chapter_names = prose_chapter_names)


@app.route("/maths")
def class_10_maths():
    cursor = db["Maths"].find({})
    data = []
    for x in cursor:
        data.append(x)
    # print(data)

    maths_chapter_names = [list(x)[1] for x in data]
    # print(maths_chapter_names)
    return render_template('Maths.html', subject = "Mathematics", maths_chapter_names=maths_chapter_names)


@app.route("/sst")
def class_10_sst():
    cursor = db["Economics"].find({})
    data = []
    for x in cursor:
        data.append(x)
    eco_chapter_names = [list(x)[1] for x in data]
    cursor = db["Geography"].find({})
    data = []
    for x in cursor:
        data.append(x)
    geo_chapter_names = [list(x)[1] for x in data]
    cursor = db["History"].find({})
    data = []
    for x in cursor:
        data.append(x)
    history_chapter_names = [list(x)[1] for x in data]
    cursor = db["Political Science"].find({})
    data = []
    for x in cursor:
        data.append(x)
    pol_science_chapter_names = [list(x)[1] for x in data]
    return render_template('Social Science.html', subject = "Social Science", geo_chapter_names=geo_chapter_names, eco_chapter_names=eco_chapter_names, history_chapter_names=history_chapter_names, pol_science_chapter_names=pol_science_chapter_names)

@app.template_filter('encode_name')
def urlquote_filter(s):
    return urllib.parse.quote(s.encode('utf-8'))

@app.template_filter('title')
def urlquote_filter(s):
    return s.title()

@app.route("/qna", defaults = {'data': 'null'})
@app.route("/qna/<data>")
def qna(data :str):
    chapter_name = data
    if data == 'null':
        return "Invalid URL"
    decoded_chapter_name = urllib.parse.unquote(chapter_name)
    decoded_chapter_name = decoded_chapter_name
    print(decoded_chapter_name, data)
    all_chapter_names = fetch_all_object_names_from_all_collections()
    if decoded_chapter_name in all_chapter_names:
        data_qna = search_objects_by_name(decoded_chapter_name)
        if decoded_chapter_name in english_chapter_names:
            print(data_qna[0])
            new_data = []
            for i in range(len(data_qna[0]) - 1):
                print(len(data_qna[0]))
                print(i)
                print(i+1)
                new_data.append({"answer_text": data_qna[0][i+1]["answer_text"], "question_text": data_qna[0][i]["question_text"]})
            data_qna[0] = new_data
                
        if decoded_chapter_name in maths_chapter_names:
                new_data = []
                for k, v in data_qna[0].items():
                    for x in v:
                        new_data.append(x)
                data_qna[0] = new_data
        if decoded_chapter_name in science_chapter_names:
                new_data = []
                for k, v in data_qna[0].items():
                    for x in v:
                        new_data.append(x)
                data_qna[0] = new_data
        return render_template("qna.html", data_qna=data_qna[0], chapter_name=decoded_chapter_name)
    if decoded_chapter_name not in all_chapter_names:
        return "Invalid URL"


if __name__ == '__main__':
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')
    app.run(debug=True, port=5000)
