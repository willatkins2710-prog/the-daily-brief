# The Daily Brief — live headlines prototype

A minimalist, UK-first general-interest digital newspaper hosted free on GitHub Pages.

## Features

- **Today:** current source-linked headlines from public RSS news feeds.
- **Sections:** UK News, World, Business (including **Supermarkets & UK Grocery**), Economy, AI, Sport (including **Sports Business**), Money, Health, Culture, TV & Film, Travel and Technology.
- **Save and search:** bookmarks for news links and original sample reading, stored locally in the browser.
- **Explore in depth:** evergreen sample essays with Quick Read, Analysis and Deep Dive modes. These are not current news reporting.

## Automatic updates

The `.github/workflows/news.yml` action collects RSS headlines using `scripts/fetch_news.py` every four hours (GitHub schedules may be delayed). It publishes a static `news.json` with `index.html`. No paid API keys.

**One-time setup:** Under **Settings → Pages → Build and deployment → Source**, choose **GitHub Actions** (not "Deploy from a branch"). This ensures the scheduled deploy includes the generated news file. See **Actions** for the last run and any feed failures.

GitHub may disable scheduled Actions for a public repository after an extended period of inactivity.

## Editorial transparency

Live items link to original publishers; full publisher articles are not copied. The app does not yet AI-research or write in-depth current articles. The existing long reads are clearly marked as demonstrations. Individual publishers may have paywalls.

## Website

https://willatkins2710-prog.github.io/the-daily-brief/
