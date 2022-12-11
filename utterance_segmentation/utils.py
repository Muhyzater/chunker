import re
from collections import namedtuple
from xml.etree import ElementTree as ET

from arabic_analysis import arabic

Verdict = namedtuple("Verdict", ["is_valid", "reason"])


def remove_tag(text: str, tag: str) -> str:

    pattern = r"<{0}>|</{0}>".format(tag)

    return re.sub(pattern, "", text)


def seperate_on_sentence(text: str) -> list:

    text = re.sub(r"(<break[^>]*>[^>]*</break>|<break[^>]*>)", r"<s>\1</s>", text)
    text = re.sub(r"(<prosody[^>]*>|</prosody>)", r"<s>\1</s>", text)

    text = re.sub(r"(<p>|</p>|<s>|</s>)", r"\1~~", text)
    return [remove_tag(remove_tag(chunk, "s"), "p") for chunk in re.split("~~", text)]


def sentence_length(text: str) -> int:

    puns = "".join(arabic.ARABIC_PUNC | arabic.ENGLISH_PUNC)
    pattern = r"[{}\s]+".format(re.escape(puns))

    return len(re.split(pattern, text))


def validate_ssml(text: str) -> Verdict:

    # TODO: write as chain of responsibility
    def is_valid_xml(text):
        try:
            return ET.fromstring(text)
        except ET.ParseError as e:
            return None

    def in_outer_only(root, tag):
        outer = root.findall(tag)
        all = root.findall(".//{}".format(tag))
        return len(all) - len(outer) == 0

    def has_no_children(element):
        return len(element) == 0

    def allowed_tags_only(element, allowed_tags):
        return all(i.tag in allowed_tags for i in element.getchildren())

    root = is_valid_xml(text)

    if root is None:
        return Verdict(False, "invalid XML")

    elif not in_outer_only(root, "break"):
        return Verdict(False, '"break" tag not in outer level')

    elif not in_outer_only(root, "prosody"):
        return Verdict(False, '"prosody" tag not in outer level')

    elif not all(has_no_children(i) for i in root.findall(".//s")):
        return Verdict(False, '"s" tags can only contain text')

    elif not all(allowed_tags_only(i, {"s"}) for i in root.findall(".//p")):
        return Verdict(False, '"p" tags can only contain text or "s" tags')

    elif not all(allowed_tags_only(i, {"s", "p"}) for i in root.findall(".//prosody")):
        return Verdict(
            False, '"prosody" tags can only contain text, "s" tags or "p" tags'
        )

    return Verdict(True, None)
