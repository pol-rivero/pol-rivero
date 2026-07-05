# Python script to render the README.md file from the template

import os
from datetime import date, datetime, timedelta

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

def format_template(content):
    content = content.replace("$[CURRENT_YEAR]", datetime.now().strftime("%Y"))
    return content

def main():
    template = get_template()
    content = format_template(template)

    output_file = os.path.join(current_dir, "README.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
