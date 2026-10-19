"""Refresh the existing profile SVG from GitHub's public repository API."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def fetch_total_stars(owner, token="", opener=urllib.request.urlopen):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", owner):
        raise ValueError("Invalid GitHub username")
    total = 0
    page = 1
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-star-updater"}
    if token:
        headers["Authorization"] = "Bearer " + token
    while True:
        url = ("https://api.github.com/users/" + urllib.parse.quote(owner)
               + f"/repos?type=owner&per_page=100&page={page}")
        with opener(urllib.request.Request(url, headers=headers), timeout=30) as response:
            repos = json.load(response)
        if not isinstance(repos, list):
            raise ValueError("GitHub returned an unexpected repository response")
        for repo in repos:
            if (repo["fork"] or repo.get("private", False)
                    or repo["owner"]["login"].casefold() != owner.casefold()):
                continue
            stars = repo["stargazers_count"]
            if type(stars) is not int or stars < 0:
                raise ValueError("Invalid star count from GitHub")
            total += stars
        if len(repos) < 100:
            return total
        page += 1


def update_svg(path, owner, total, checked_at):
    if type(total) is not int or total < 0:
        raise ValueError("Total stars must be a non-negative integer")
    root = ET.fromstring(path.read_bytes())
    nodes = {node.get("id"): node for node in root.iter() if node.get("id")}
    for required in ("t", "d", "star-count", "stats-updated"):
        if required not in nodes:
            raise ValueError("Missing SVG element: " + required)
    local_time = checked_at.astimezone(timezone(timedelta(hours=7)))
    stamp = local_time.strftime("%d %b %Y %H:%M").upper() + " GMT+7"
    display = f"{total:02d}"
    nodes["star-count"].text = display
    nodes["star-count"].set("font-size", f"{min(65, 108 / (len(display) * .62)):.1f}")
    nodes["stats-updated"].text = "UPDATED / " + stamp
    nodes["t"].text = f"{total} stars received"
    nodes["d"].text = ("Total stars received across public repositories owned by " + owner
                       + ", excluding forks. Updated " + stamp + ".")
    output = ET.tostring(root, encoding="utf-8") + b"\n"
    if output == path.read_bytes():
        return
    # API or validation failures leave the previous good SVG in place.
    temporary = path.with_suffix(".svg.tmp")
    temporary.write_bytes(output)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default=os.environ.get("PROFILE_OWNER", "thanhdo257205"))
    parser.add_argument("--svg", type=Path, default=Path(__file__).resolve().parents[1] / "assets/stars.svg")
    args = parser.parse_args()
    total = fetch_total_stars(args.owner, os.environ.get("GH_TOKEN", ""))
    update_svg(args.svg, args.owner, total, datetime.now(timezone.utc))
    print(f"Updated public non-fork repository stars: {total}")


if __name__ == "__main__":
    main()
