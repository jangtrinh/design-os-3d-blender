#!/usr/bin/env python3
"""Report unbalanced or unclosed tags in a generated HTML page.

    python3 scripts/check-html-tag-balance.py docs/reviews/dc-01/r03/index.html

`ui gate` only reports the last symptom of a broken nesting ("41 open, 40 close"),
so run this first after any edit to a shipped page. Exit 0 clean, 1 unbalanced.
"""

import sys
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "source", "track", "wbr"}


class TagStack(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.mismatched = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1][0] != tag:
            self.mismatched.append((tag, self.getpos(), self.stack[-1] if self.stack else None))
        else:
            self.stack.pop()


def main(paths):
    failed = False
    for path in paths:
        parser = TagStack()
        parser.feed(open(path, encoding="utf-8").read())
        for tag, pos, expected in parser.mismatched:
            print(f"{path}:{pos[0]}: </{tag}> closes nothing"
                  f"{' (open: <' + expected[0] + '> from line ' + str(expected[1][0]) + ')' if expected else ''}")
            failed = True
        for tag, pos in parser.stack:
            print(f"{path}:{pos[0]}: <{tag}> never closed")
            failed = True
        if not parser.mismatched and not parser.stack:
            print(f"{path}: balanced")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    raise SystemExit(main(sys.argv[1:]))
