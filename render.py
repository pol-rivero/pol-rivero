# Python script to render the README.md file from the template

import os
import random
import requests
from datetime import *

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

this_month = datetime.now().replace(day=1)
if this_month.month == 1:
    last_month = this_month.replace(year=this_month.year - 1, month=12)
else:
    last_month = this_month.replace(month=this_month.month - 1)
num_commits = get_commits(last_month, this_month)

content = content.replace("$[NUM_COMMITS]", str(num_commits))
content = content.replace("$[LAST_MONTH]", last_month.strftime("%B %Y"))



# Use numbersapi to get a random fact about the number of commits
def get_fact(num):
    if random.random() < .5:
        url = "http://numbersapi.com/" + str(num) + "/math"
    else:
        url = "http://numbersapi.com/" + str(num) + "/trivia"
    response = requests.get(url)
    if response.status_code != 200:
        print("Could not get fact:")
        print(response.text)
        return "N/A"
    else:
        return str(response.text)

if (num_commits == "N/A"):
    commits_comment = "It seems that the GitHub API is down 💀"
elif (num_commits == 0):
    commits_comment = "I was probably taking a break ⛱"
elif (num_commits == 1):
    commits_comment = "I bet it's feeling lonely..."
else:
    commits_comment = "Fun fact: " + get_fact(num_commits) + " 🤓"
    
content = content.replace("$[COMMITS_COMMENT]", commits_comment)


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

# September 19th is International Talk Like a Pirate Day
if (date.today().month == 9 and date.today().day == 19):    
    content = piratify(content)

# Write the output file
with open(output_file, "w") as f:
    f.write(content)
