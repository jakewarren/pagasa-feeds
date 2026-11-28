# PAGASA Feeds

This repository publishes RSS feeds built from advisories on the [PAGASA](https://www.pagasa.dost.gov.ph) regional forecast pages. It aggregates rainfall advisories, thunderstorm advisories, and special forecasts into machine-readable feeds that can be consumed by feed readers or other services.

Each feed corresponds to a PAGASA regional slug (for example, `visprsd` for the Visayas). GitHub Actions periodically scrape the corresponding regional page and update the RSS file under the `rss-feed` branch so subscribers can stay informed about the latest advisories.

## Feeds
 
| Region  | Feed Link |
|---------|-----------|
| Visayas |  [![RSS](https://img.shields.io/badge/rss-F88900?style=for-the-badge&logo=rss&logoColor=white)](https://jakewarren.github.io/pagasa-feeds/visprsd.rss)    |
| National Capital Region | [![RSS](https://img.shields.io/badge/rss-F88900?style=for-the-badge&logo=rss&logoColor=white)](https://jakewarren.github.io/pagasa-feeds/ncrprsd.rss) |
