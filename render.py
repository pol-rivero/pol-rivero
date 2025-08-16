# Python script to render the README.md file from the template

import os
from datetime import date, datetime, timedelta

import requests
from openai import OpenAI

current_dir = os.path.dirname(os.path.realpath(__file__))


def get_template_name():
    special_template = "special/" + date.today().strftime("%m-%d") + ".md"
    if os.path.isfile(special_template):
        return special_template
    return "TEMPLATE.md"


def get_template():
    input_file = os.path.join(current_dir, get_template_name())
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def get_commits(start_date, end_date):
    "Use the GitHub API to get the number of commits in a date range"
    url = "https://api.github.com/search/commits"
    headers = {"Accept": "application/vnd.github.v3+json"}
    params = {"q": "author:pol-rivero committer-date:" +
              start_date.strftime("%Y-%m-%d") + ".." + end_date.strftime("%Y-%m-%d")}
    response = requests.get(url, headers=headers, params=params, timeout=15)
    if response.status_code != 200:
        print("Could not get commits:")
        print(response.text)
        return "N/A"
    else:
        return response.json()["total_count"]


def get_commits_this_month():
    "Get the number of commits in the current month"
    this_month = datetime.now().replace(day=1)
    if this_month.month == 1:
        last_month = this_month.replace(year=this_month.year - 1, month=12)
    else:
        last_month = this_month.replace(month=this_month.month - 1)
    return get_commits(last_month, this_month)


def get_tech_haiku():
    "Generate haiku based on tech news"
    def get_tech_news(api_key, num_stories=4):
        current_date = datetime.now()
        from_date = (current_date - timedelta(days=5)).strftime("%Y-%m-%d")
        to_date = current_date.strftime("%Y-%m-%d")
        try:
            query_json = str({
                "$query": {
                    "$and": [
                        {
                            "$or": [
                                {"categoryUri": "dmoz/Science/Technology"},
                                {"categoryUri": "dmoz/Computers"},
                            ]
                        },
                        {"sourceUri": "arstechnica.com"},
                        {"dateStart": from_date, "dateEnd": to_date, "lang": "eng"},
                    ]
                }
            }).replace("'", '"')
            query = requests.utils.quote(query_json)
            url = f"https://newsapi.ai/api/v1/event/getEvents?query={query}&resultType=events&eventsSortBy=date&includeEventSummary=true&includeEventLocation=false&includeEventArticleCounts=false&includeEventStories=true&includeStoryMedoidArticle=true&includeEventConcepts=false&includeEventCategories=false&eventImageCount=1&storyImageCount=1&apiKey={api_key}"
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                print("Could not get tech news:")
                print(response.text)
                return None
            events = response.json()["events"]["results"]
            if len(events) == 0:
                print("No tech news found. Response:")
                print(response.text)
                return None

            def str_event(event):
                title = event["title"]["eng"]
                summary = event["summary"]["eng"]
                url = event["stories"][0]["medoidArticle"]["url"]
                return f"{title}\n{summary}\nURL: {url}\nEND STORY"
            return [str_event(event) for event in events[:num_stories]]
        except Exception as e:
            print("Error getting tech news:")
            print(e)
            return None

    def get_haiku(news):
        if news is None:
            return "Failed API call,\nBits and bytes lost in the void,\nSilent tech news cries."
        client = OpenAI()
        response = client.responses.create(
            model="gpt-5",
            instructions="You are an AI poet writing haikus. The user provides a summary of some tech news stories, and you respond with only one haiku, which should be about one of the stories. After the 3 lines of the haiku, add one extra line with the URL of the story you wrote about.",
            input="\n\n".join(news)
        )
        response_lines = response.output_text.split("\n")
        haiku = "\n".join(response_lines[:3])
        urls = [line.removeprefix("URL:").strip()
                for line in response_lines[3:]]
        return (haiku, urls)

    newsapi_key = os.getenv("NEWSAPI_KEY").split(",")
    news_results = None
    for key in newsapi_key:
        if news_results is None:
            news_results = get_tech_news(key)
    return get_haiku(news_results)


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


def is_talk_like_a_pirate_day():
    return date.today().month == 9 and date.today().day == 19


def get_age():
    birthday = datetime(2001, 6, 25)
    return (datetime.now() - birthday).days // 365


def format_template(content):
    content = content.replace(
        "$[CURRENT_DATE]", datetime.now().strftime("%B %-d, %Y"))
    content = content.replace("$[CURRENT_YEAR]", datetime.now().strftime("%Y"))
    content = content.replace("$[CURRENT_AGE]", str(get_age()))
    content = content.replace("$[NUM_COMMITS]", str(get_commits_this_month()))
    if "$[TECH_HAIKU]" in content:
        haiku, urls = get_tech_haiku()
        content = content.replace("$[TECH_HAIKU]", haiku)
        content = content.replace("$[TECH_HAIKU_URLS]", "\n\n".join(urls))
    return content


def main():
    template = get_template()
    content = format_template(template)

    if is_talk_like_a_pirate_day():
        content = piratify(content)

    output_file = os.path.join(current_dir, "README.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
