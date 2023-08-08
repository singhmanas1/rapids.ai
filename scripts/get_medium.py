import requests
import xmltodict
import yaml

from html.parser import HTMLParser
from pathlib import Path


class SummaryParser(HTMLParser):
    """
    Parses HTML content and stores all of the text from paragraph elements in
    "self.all_p_data".
    """

    def __init__(self):
        HTMLParser.__init__(self)
        self.in_p_tag = False
        self.current_p_data = ""
        self.all_p_data = []

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.in_p_tag = True

    def handle_endtag(self, tag):
        if tag == "p":
            self.in_p_tag = False
            self.all_p_data.append(self.current_p_data)
            self.current_p_data = ""

    def handle_data(self, data):
        if self.in_p_tag:
            self.current_p_data += data


def is_author_element(p):
    """
    Returns True if the given paragraph text contains author information.
    """
    return ("Authors" in p) or ("By:" in p)


def get_summary(rssContent):
    """
    Returns a 270 character summary of a Medium article given it's full content
    as retrieved from their RSS feed.
    """
    parser = SummaryParser()
    parser.feed(rssContent)
    article_content = " ".join(
        [p for p in parser.all_p_data if not is_author_element(p)]
    )
    if article_content:
        return article_content[:267] + "..."
    return ""


def write_posts_to_file(posts):
    """
    Writes the posts data to a YAML file that can be used by Hugo.
    """
    script_path = Path(__file__)
    script_name = script_path.name
    current_dir = script_path.parent
    output_file = current_dir.joinpath("..", "data", "posts", "medium.yaml")
    header = "\n".join(
        ["#", f'# This file was automatically generated by "{script_name}"', "#"]
    )
    with open(output_file, "w") as file:
        file.write("\n".join([header, yaml.dump(posts)]))


def main():
    """
    Retrieves latests RAPIDS posts from Medium's RSS feed and writes the content
    to a YAML file that can be used by Hugo.
    """
    response = requests.get("https://medium.com/feed/rapids-ai")
    xml = xmltodict.parse(response.content)
    posts = []

    for x in xml["rss"]["channel"]["item"]:
        post = {}
        post["title"] = x["title"]
        post["link"] = x["link"].split("?")[0]
        post["poster"] = x["dc:creator"]
        post["date"] = x["pubDate"]
        post["text"] = get_summary(x["content:encoded"])
        posts.append(post)

    write_posts_to_file(posts)


if __name__ == "__main__":
    main()