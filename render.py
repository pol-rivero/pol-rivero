# Python script to render the README.md file from the template

import os
from datetime import date, datetime, timedelta

import requests
from openai import OpenAI


# If there's a special template for today, use that. Otherwise, use the default template
def get_template():
    special_template = "special/" + date.today().strftime("%m-%d") + ".md"
    if os.path.isfile(special_template):
        return special_template
    return "TEMPLATE.md"


# Get the input and output filenames
current_dir = os.path.dirname(os.path.realpath(__file__))
input_file = os.path.join(current_dir, get_template())
output_file = os.path.join(current_dir, "README.md")

# Read the template file
with open(input_file, "r") as f:
    content = f.read()

# Get the current date
content = content.replace("$[CURRENT_DATE]", datetime.now().strftime("%B %-d, %Y"))
content = content.replace("$[CURRENT_YEAR]", datetime.now().strftime("%Y"))

# Compute my age
birthday = datetime(2001, 6, 25)
age = (datetime.now() - birthday).days // 365
content = content.replace("$[CURRENT_AGE]", str(age))



# Use the GitHub API to get the number of commits
def get_commits(start_date, end_date):
    url = "https://api.github.com/search/commits"
    headers = {"Accept": "application/vnd.github.v3+json"}
    params = {"q": "author:p-rivero committer-date:" + start_date.strftime("%Y-%m-%d") + ".." + end_date.strftime("%Y-%m-%d")}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print("Could not get commits:")
        print(response.text)
        return "N/A"
    else:
        return response.json()["total_count"]

# Generate haiku based on tech news
def get_tech_haiku():
    def get_tech_news(api_key, num_stories=5):
        current_date = datetime.now()
        from_date = (current_date - timedelta(days=5)).strftime("%Y-%m-%d")
        to_date = current_date.strftime("%Y-%m-%d")
        try:
            url = f"https://newsapi.ai/api/v1/event/getEvents?query=%7B%22%24query%22%3A%7B%22%24and%22%3A%5B%7B%22categoryUri%22%3A%22dmoz%2FComputers%22%7D%2C%7B%22sourceUri%22%3A%22arstechnica.com%22%7D%2C%7B%22dateStart%22%3A%22{from_date}%22%2C%22dateEnd%22%3A%22{to_date}%22%2C%22lang%22%3A%22eng%22%7D%5D%7D%7D&resultType=events&eventsSortBy=date&includeEventSummary=true&includeEventLocation=false&includeEventArticleCounts=false&includeEventConcepts=false&includeEventCategories=false&eventImageCount=1&storyImageCount=1&apiKey={api_key}"
            response = requests.get(url)
            if response.status_code != 200:
                print("Could not get tech news:")
                print(response.text)
                return None
            events = response.json()["events"]["results"]
            if len(events) == 0:
                print("No tech news found")
                return None
            return [event["title"]["eng"] + "\n" + event["summary"]["eng"] + "\nEND STORY" for event in events[:num_stories]]
        except Exception as e:
            print("Error getting tech news:")
            print(e)
            return None
            
    def get_haiku(news):
        if news is None:
            return "Failed API call,\nBits and bytes lost in the void,\nSilent tech news cries."
        system_prompt = "You are an AI poet writing haikus. The user provides a summary of some tech news stories, and you respond with only one haiku, which should be about one or more of the stories."
        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "\n\n".join(news)},
            ]
        )
        return completion.choices[0].message.content

    newsapi_key = os.getenv("NEWSAPI_KEY")
    return get_haiku(get_tech_news(newsapi_key))

def piratify(text):
    url = "https://api.funtranslations.com/translate/pirate.json"
    response = requests.post(url, data={"text": text})
    if response.status_code != 200:
        print("Could not piratify text:")
        print(response.text)
        return text
    else:
        start = "Ahoy matey! Happy [International Talk Like a Pirate Day](https://en.wikipedia.org/wiki/International_Talk_Like_a_Pirate_Day)!\n\n"
        return start + response.json()["contents"]["translated"]

this_month = datetime.now().replace(day=1)
if this_month.month == 1:
    last_month = this_month.replace(year=this_month.year - 1, month=12)
else:
    last_month = this_month.replace(month=this_month.month - 1)
num_commits = get_commits(last_month, this_month)

content = content.replace("$[NUM_COMMITS]", str(num_commits))
content = content.replace("$[LAST_MONTH]", last_month.strftime("%B %Y"))
if "$[TECH_HAIKU]" in content:
    content = content.replace("$[TECH_HAIKU]", get_tech_haiku())

# September 19th is International Talk Like a Pirate Day
if (date.today().month == 9 and date.today().day == 19):    
    content = piratify(content)

# Write the output file
with open(output_file, "w") as f:
    f.write(content)
