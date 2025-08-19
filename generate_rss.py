#!/usr/bin/env python3
"""Generate RSS feed for PAGASA regional advisories."""
import argparse
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape, unescape

import requests
from bs4 import BeautifulSoup
from xml.etree.ElementTree import (
    Element,
    SubElement,
    ElementTree,
    fromstring,
    indent,
    ParseError,
)


def safe_fromstring(html_content):
    """Safely parse HTML content, handling malformed HTML gracefully."""
    try:
        return fromstring(f"<div>{html_content}</div>")
    except ParseError:
        # Fallback: preserve visual line breaks and avoid XML entity errors
        # 1) Convert HTML named entities to Unicode to sidestep XML named entity issues (e.g., &nbsp;)
        text = unescape(html_content)
        # 2) Split on <br> variants and build mixed content safely without XML parsing
        parts = re.split(r'(?i)<br\s*/?>', text)
        root = Element("div")
        if parts:
            root.text = parts[0]
            for piece in parts[1:]:
                SubElement(root, "br").tail = piece
        else:
            # As a last resort, escape the text but keep it renderable
            root.text = text
        return root

def normalize_html(html):
    """Normalize HTML content for consistent formatting."""
    if not html:
        return ""
    
    # Remove extra whitespace and newlines
    html = re.sub(r'\s+', ' ', html.strip())
    
    # Normalize br tags to self-closing format
    html = re.sub(r'<br\s*/?>', '<br />', html, flags=re.IGNORECASE)
    
    # Remove closing br tags which are invalid
    html = html.replace('</br>', '')
    
    return html


def add_items(soup, channel, div_id, category, slug):
    """Add RSS items from a specific div section."""
    div = soup.find("div", id=div_id)
    if not div:
        return
        
    if div_id == "special-forecasts":
        for link in div.find_all("a"):
            href = link.get("href")
            title = link.get_text(strip=True)
            
            # Extract and join span content with line breaks
            spans = [s.get_text(strip=True) for s in link.find_all("span")]
            parts = [p for p in spans if p]
            
            if parts:
                html = "<br />".join(parts)
            else:
                # Fallback to full link text with br separators
                html = link.get_text(separator="<br />", strip=True)
            
            # Create RSS item
            item = SubElement(channel, "item")
            SubElement(item, "title").text = f"{category}: {title}" if title else category
            
            if href:
                # Ensure href is absolute URL
                if href.startswith('/'):
                    href = f"https://www.pagasa.dost.gov.ph{href}"
                SubElement(item, "link").text = href
            
            if html:
                desc = SubElement(item, "description")
                try:
                    frag = safe_fromstring(html)
                    desc.text = frag.text or ""
                    for child in list(frag):
                        desc.append(child)
                except Exception:
                    # Ultimate fallback: plain text
                    desc.text = BeautifulSoup(html, 'html.parser').get_text()
                    
            SubElement(item, "category").text = category
            
    else:
        for entry in div.find_all("div"):
            html = entry.decode_contents()
            html = normalize_html(html)
            
            if not html.strip():
                continue
            
            # Extract advisory number with improved regex
            match = re.search(r'(?:No|Number)\.?\s*(\d+)', html, re.IGNORECASE)
            number = match.group(1) if match else None
            
            # Create title with proper formatting
            if number:
                title = f"{category} No. {number} #{slug.upper()}"
            else:
                title = f"{category} #{slug.upper()}"
            
            # Create RSS item
            item = SubElement(channel, "item")
            SubElement(item, "title").text = title
            
            desc = SubElement(item, "description")
            try:
                frag = safe_fromstring(html)
                desc.text = frag.text or ""
                for child in list(frag):
                    desc.append(child)
            except Exception:
                # Ultimate fallback: plain text
                desc.text = BeautifulSoup(html, 'html.parser').get_text()
                
            SubElement(item, "category").text = category


def main(slug: str) -> None:
    """Generate RSS feed for PAGASA regional advisories."""
    url = f"https://www.pagasa.dost.gov.ph/regional-forecast/{slug}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return
    
    soup = BeautifulSoup(response.content, "html.parser")

    # Create RSS structure
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = f"PAGASA {slug.upper()} Advisories"
    SubElement(channel, "link").text = url
    SubElement(channel, "description").text = (
        f"Aggregated rainfall, thunderstorm, and special forecasts from PAGASA {slug.upper()}"
    )
    SubElement(channel, "lastBuildDate").text = format_datetime(
        datetime.now(timezone.utc)
    )

    # Add items from different sections
    add_items(soup, channel, "rainfalls", "Rainfall Advisory", slug)
    add_items(soup, channel, "thunderstorms", "Thunderstorm Advisory", slug)
    add_items(soup, channel, "special-forecasts", "Special Forecast", slug)

    # Write RSS file
    try:
        indent(rss, space="  ")
        tree = ElementTree(rss)
        tree.write(f"{slug}.rss", encoding="utf-8", xml_declaration=True)
        print(f"Successfully generated {slug}.rss")
    except Exception as e:
        print(f"Error writing RSS file: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate PAGASA RSS feed")
    parser.add_argument("slug", help="PAGASA regional forecast slug, e.g., visprsd")
    args = parser.parse_args()
    main(args.slug)
