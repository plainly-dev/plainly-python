"""A tiny HTML reader, so tests can ask "what text is in `#pipeline-lead`?" without BeautifulSoup.

Supported selectors (all that the tests need):

    tag   .class   #id   [attr]   [attr=value]      and combinations such as  tr[data-contact-id] .name
    a space between two selectors means "somewhere inside" (descendant).

The page must be well-formed enough: every element is explicitly closed (no omitted </li>, </td>, </tr>, </p>).
"""

import re
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SILENT = {"script", "style"}  # their content is code, never visible text


class Node:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = dict(attrs or {})
        self.parent = parent
        self.children = []  # Node or str

    def classes(self):
        return (self.attrs.get("class") or "").split()

    def text(self):
        """Visible text of this element and everything inside it, with whitespace collapsed."""
        pieces = []

        def walk(node):
            for child in node.children:
                if isinstance(child, str):
                    pieces.append(child)
                elif child.tag not in SILENT:
                    walk(child)

        walk(self)
        return " ".join("".join(pieces).split())

    def descendants(self):
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.descendants()

    def select(self, selector):
        steps = [_parse_step(part) for part in selector.split()]
        found = []
        for node in self.descendants():
            if _matches(node, steps[-1]) and _ancestors_match(node, steps[:-1], stop=self):
                found.append(node)
        return found

    def select_one(self, selector):
        found = self.select(selector)
        return found[0] if found else None


def _parse_step(step):
    tag = re.match(r"[a-zA-Z][a-zA-Z0-9]*", step)
    rest = step[tag.end():] if tag else step
    conditions = []
    for token in re.findall(r"#[\w-]+|\.[\w-]+|\[[^\]]+\]", rest):
        if token[0] == "#":
            conditions.append(("id", token[1:]))
        elif token[0] == ".":
            conditions.append(("class", token[1:]))
        else:
            name, _, value = token[1:-1].partition("=")
            conditions.append(("attr", name, value.strip("'\"") if _ else None))
    return (tag.group(0).lower() if tag else None, conditions)


def _matches(node, step):
    tag, conditions = step
    if tag and node.tag != tag:
        return False
    for condition in conditions:
        kind = condition[0]
        if kind == "id" and node.attrs.get("id") != condition[1]:
            return False
        if kind == "class" and condition[1] not in node.classes():
            return False
        if kind == "attr":
            _, name, value = condition
            if name not in node.attrs or (value is not None and node.attrs[name] != value):
                return False
    return True


def _ancestors_match(node, steps, stop):
    parent = node.parent
    for step in reversed(steps):
        while parent is not None and parent is not stop and not _matches(parent, step):
            parent = parent.parent
        if parent is None or parent is stop:
            return False
        parent = parent.parent
    return True


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.stack[-1])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        for depth in range(len(self.stack) - 1, 0, -1):
            if self.stack[depth].tag == tag:
                del self.stack[depth:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse(html):
    builder = _Builder()
    builder.feed(html)
    builder.close()
    return builder.root
