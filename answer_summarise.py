from transformers import pipeline, T5Tokenizer

paragraph = """
    The tiger in the poem is wretched in its cage. It longs for freedom. It may be well looked after, but the fact of the matter is that unless one is free, one is not alive. Confinement brings bondage, and bondage is cruel. One may argue that at least this way they all will not be killed and become extinct. However, taking away one’s freedom to keep one alive kill the desire to live anyhow. Even humans throughout the world oppose the chains of slavery and oppression. How are other living creatures any different? Humans have encroached on their space, and sheltering them in zoos is truly inhuman. Humans must learn to respect nature, for humans exist only due to nature.
"""

summarizer = pipeline("summarization", model="t5-base", max_length=int(len(paragraph.split(' '))/1.5))


summary = summarizer(paragraph)
print(summary)

generated_summary = summary[0]['summary_text'].strip()

# Splitting the generated summary into 5 points
points = generated_summary.split('. ')

# Printing the 5 points with headings
for i, point in enumerate(points):
    print(f"Point {i+1}: {point}")
