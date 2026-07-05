# Renders README.md.
#
# On a "special" day (a special/MM-DD.md template exists for today) that template
# is used. Otherwise the project rows are (re)generated as SVGs and the README is
# assembled from them by generate_svgs.generate().

import os
from datetime import date, datetime

import generate_svgs

current_dir = os.path.dirname(os.path.realpath(__file__))


def special_template():
    """Return today's special template content (formatted), or None."""
    path = os.path.join(current_dir, "special", date.today().strftime("%m-%d") + ".md")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return format_template(f.read())


def format_template(content):
    return content.replace("$[CURRENT_YEAR]", datetime.now().strftime("%Y"))


def main():
    content = special_template()
    if content is None:
        content = generate_svgs.generate()

    output_file = os.path.join(current_dir, "README.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
