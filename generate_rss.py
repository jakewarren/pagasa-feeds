#!/usr/bin/env python3
"""Generate RSS feed for PAGASA regional advisories."""
import argparse
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
import xml.dom.minidom
from xml.etree.ElementTree import Element, SubElement, tostring


def add_items(soup, channel, div_id, category, slug):
    div = soup.find("div", id=div_id)
    if not div:
        return
    if div_id == "special-forecasts":
        for link in div.find_all("a"):
            href = link.get("href")
            title = link.get_text(strip=True)
            spans = [s.get_text(strip=True) for s in link.find_all("span")]
            description = "<br />".join(spans)
            item = SubElement(channel, "item")
            SubElement(item, "title").text = f"{category}: {title}" if title else category
            if href:
                SubElement(item, "link").text = href
            if description:
                SubElement(item, "description").text = description
            SubElement(item, "category").text = category
    else:
        for entry in div.find_all("div"):
            html = entry.decode_contents().replace("\n", "")
            if not html.strip():
                continue
            match = re.search(r"No\.\s*(\d+)", html, re.IGNORECASE)
            number = match.group(1) if match else None
            title = (
                f"{category} No. {number} #{slug.upper()}" if number else category
            )
            item = SubElement(channel, "item")
            SubElement(item, "title").text = title
            SubElement(item, "description").text = html
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
    SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    add_items(soup, channel, "rainfalls", "Rainfall Advisory", slug)
    add_items(soup, channel, "thunderstorms", "Thunderstorm Advisory", slug)
    add_items(soup, channel, "special-forecasts", "Special Forecast", slug)

    xml_bytes = tostring(rss, encoding="utf-8")
    dom = xml.dom.minidom.parseString(xml_bytes)
    for desc in dom.getElementsByTagName("description"):
        if desc.firstChild:
            text = desc.firstChild.data
            desc.removeChild(desc.firstChild)
            desc.appendChild(dom.createCDATASection(text))
    pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8")
    with open(f"{slug}.rss", "wb") as f:
        f.write(pretty_xml)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate PAGASA RSS feed")
    parser.add_argument("slug", help="PAGASA regional forecast slug, e.g., visprsd")
    args = parser.parse_args()
    main(args.slug)
