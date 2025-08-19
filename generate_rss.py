#!/usr/bin/env python3
"""Generate RSS feed for PAGASA regional advisories."""
import argparse
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from xml.etree.ElementTree import Element, ElementTree, SubElement


def add_items(soup, channel, div_id, category, slug):
    div = soup.find("div", id=div_id)
    if not div:
        return
    if div_id == "special-forecasts":
        for link in div.find_all("a"):
            href = link.get("href")
            title = link.get_text(strip=True)
            spans = [s.get_text(strip=True) for s in link.find_all("span")]
            description = " ".join(spans)
            item = SubElement(channel, "item")
            SubElement(item, "title").text = f"{category}: {title}" if title else category
            if href:
                SubElement(item, "link").text = href
            if description:
                SubElement(item, "description").text = description
            SubElement(item, "category").text = category
    else:
        for entry in div.find_all("div"):
            text = entry.get_text(strip=True)
            if not text:
                continue
            match = re.search(r"No\.\s*(\d+)", text, re.IGNORECASE)
            number = match.group(1) if match else None
            title = (
                f"{category} No. {number} #{slug.upper()}" if number else category
            )
            item = SubElement(channel, "item")
            SubElement(item, "title").text = title
            SubElement(item, "description").text = text
            SubElement(item, "category").text = category


def main(slug: str) -> None:
    url = f"https://www.pagasa.dost.gov.ph/regional-forecast/{slug}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = f"PAGASA {slug.upper()} Advisories"
    SubElement(channel, "link").text = url
    SubElement(channel, "description").text = (
        f"Aggregated rainfall, thunderstorm, and special forecasts from PAGASA {slug.upper()}"
    )
    SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    add_items(soup, channel, "rainfalls", "Rainfall Advisory", slug)
    add_items(soup, channel, "thunderstorms", "Thunderstorm Advisory", slug)
    add_items(soup, channel, "special-forecasts", "Special Forecast", slug)

    tree = ElementTree(rss)
    tree.write(f"{slug}.rss", encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate PAGASA RSS feed")
    parser.add_argument("slug", help="PAGASA regional forecast slug, e.g., visprsd")
    args = parser.parse_args()
    main(args.slug)
