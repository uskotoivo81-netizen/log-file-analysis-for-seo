#!/usr/bin/env python3
"""Summarize combined access logs for Googlebot-looking requests.

Stdlib only. Groups status codes, first path segment, 404 prefixes,
and smartphone vs desktop Googlebot user-agents.

Usage:
    python3 summarize_googlebot_log.py access.log
"""

from __future__ import print_function

import collections
import re
import sys
import urllib.parse

# Combined log: IP ident user [date] "METHOD PATH PROTO" status size "ref" "ua"
COMBINED = re.compile(
    r"^\S+ \S+ \S+ \[.*?\] "
    r'"(?P<method>[A-Z]+) (?P<path>\S+) [^"]+" '
    r"(?P<status>\d{3}) \S+ "
    r'"[^"]*" "(?P<ua>[^"]*)"'
)

GOOGLEBOT_HTML = "Googlebot/2.1"
OTHER_GOOGLE = (
    "Googlebot-Image",
    "Googlebot-Video",
    "Googlebot-News",
    "Google-InspectionTool",
    "Storebot-Google",
    "Google-Extended",
)


def ua_class(ua):
    if GOOGLEBOT_HTML in ua:
        if "Mobile" in ua:
            return "smartphone"
        return "desktop"
    for token in OTHER_GOOGLE:
        if token in ua:
            return "other-google"
    if "Googlebot" in ua:
        return "other-google"
    return None


def path_prefix(path):
    parsed = urllib.parse.urlsplit(path)
    segments = [part for part in parsed.path.split("/") if part]
    if not segments:
        return "/"
    return "/" + segments[0]


def query_template(path):
    parsed = urllib.parse.urlsplit(path)
    if not parsed.query:
        return ""
    keys = sorted(urllib.parse.parse_qs(parsed.query, keep_blank_values=True))
    return "?" + "&".join("%s=" % key for key in keys)


def summarize(path):
    status_counts = collections.Counter()
    ua_counts = collections.Counter()
    prefix_counts = collections.Counter()
    not_found = collections.Counter()
    skipped = 0
    with open(path, encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            match = COMBINED.match(raw.rstrip("\n"))
            if not match:
                skipped += 1
                continue
            klass = ua_class(match.group("ua"))
            if not klass:
                continue
            ua_counts[klass] += 1
            if klass == "other-google":
                continue
            status = match.group("status")
            req_path = match.group("path")
            status_counts[status] += 1
            prefix_counts[path_prefix(req_path) + query_template(req_path)] += 1
            if status == "404":
                not_found[path_prefix(req_path)] += 1
    return status_counts, ua_counts, prefix_counts, not_found, skipped


def print_counter(title, counter, limit=20):
    print("# " + title)
    if not counter:
        print("(none)")
        print()
        return
    for key, value in counter.most_common(limit):
        print("%s\t%s" % (key, value))
    print()


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: python3 summarize_googlebot_log.py access.log")
    status_counts, ua_counts, prefix_counts, not_found, skipped = summarize(argv[1])
    print_counter("status", status_counts)
    print_counter("ua", ua_counts)
    print_counter("path", prefix_counts)
    print_counter("404 prefix", not_found)
    print("# skipped_lines\t%s" % skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
