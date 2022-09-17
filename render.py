# Python script to render the README.md file from the template

import os
import random
import requests
import datetime

# Get the input and output filenames
current_dir = os.path.dirname(os.path.realpath(__file__))
template_file = os.path.join(current_dir, "TEMPLATE.md")
output_file = os.path.join(current_dir, "README.md")

# Read the template file
with open(template_file, "r") as f:
    content = f.read()

# Get the current date
current_date = datetime.datetime.now().strftime("%B %d, %Y")
content = content.replace("$[CURRENT_DATE]", current_date)

# Compute my age
birthday = datetime.datetime(2001, 6, 25)
age = (datetime.datetime.now() - birthday).days // 365
content = content.replace("$[CURRENT_AGE]", str(age))



# Use the GitHub API to get the number of commits
def get_commits(start_date, end_date):
    url = "https://api.github.com/search/commits"
    headers = {"Accept": "application/vnd.github.v3+json"}
    params = {"q": "author:p-rivero committer-date:" + start_date.strftime("%Y-%m-%d") + ".." + end_date.strftime("%Y-%m-%d")}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return "N/A"
    else:
        return response.json()["total_count"]

this_month = datetime.datetime.now().replace(day=1)
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
        return "N/A"
    else:
        return str(response.text)

if (num_commits == "N/A"):
    commits_comment = "It seems that the GitHub API is down 💀"
elif (num_commits == 0):
    commits_comment = "I was probably taking a break ⛱"
elif (num_commits == 1):
    commits_comment = "I bet it feels lonely..."
else:
    commits_comment = "Fun fact: " + get_fact(num_commits) + " 🤓"
    
content = content.replace("$[COMMITS_COMMENT]", commits_comment)



# Write the output file
with open(output_file, "w") as f:
    f.write(content)
