# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python data scraping tool that collects supermarket company information from 7 major Japanese trade associations. The application generates structured JSON data containing company details, websites, and associated supermarket brands across Japanese prefectures.

## Development Commands

### Environment Setup
```bash
# Install dependencies using UV (modern Python package manager)
uv sync

# Install development dependencies
uv sync --group dev
```

### Running the Application
```bash
# Execute the main scraping script
uv run python main.py

# This generates data.json with scraped supermarket data
```

### Code Quality
```bash
# Format and sort imports
uv run isort main.py

# Lint and format code
uv run ruff check main.py
uv run ruff format main.py
```

## Architecture

### Core Structure
- **Single-file application** (`main.py`) - Contains all scraping logic
- **Sequential scraping** - Each function targets a specific trade association
- **Data aggregation** - Combines results from all sources into unified JSON

### Data Sources
The application scrapes from these Japanese trade associations:
1. **NSAJ** (全国スーパーマーケット協会)
2. **JSA** (日本スーパーマーケット協会)
3. **AJS** (オール日本スーパーマーケット協会) - PDF processing
4. **JCSA** (日本チェーンストア協会)
5. **CGC** (シジシージャパン)
6. **Nichiryu** (日本流通産業)
7. **Selco** (協同組合セルコチェーン)

### Data Structure
Each record contains:
```python
{
  "prefecture": str,        # Japanese prefecture
  "company_url": str,       # Company website URL
  "company_name": str,      # Company name
  "supermarket_names": []   # Associated supermarket brands
}
```

### Key Dependencies
- **bs4** - HTML parsing for web scraping
- **pymupdf** - PDF processing (used for AJS association)
- **requests** - HTTP client for web requests

## Development Notes

### Language and Localization
- All data, comments, and region mappings are in Japanese
- Code focuses specifically on Japanese retail market
- Prefecture/region mapping covers all 47 Japanese prefectures

### Code Patterns
- **Functional approach** - Each scraper is a separate function
- **Error handling** - Basic HTTP error handling with try/catch blocks
- **Type annotations** - Uses modern Python typing with Literal types
- **Regional mapping** - Comprehensive Japanese prefecture definitions

### File Organization
- `main.py` - Complete application logic
- `data.json` - Generated output (130KB+ of supermarket data)
- `super/` - Archive directory with previous data formats (JSON, YAML, CSV)
- `pyproject.toml` - Modern Python project configuration with UV

### Development Workflow
1. Modify scraping functions in `main.py` for specific trade associations
2. Run `uv run python main.py` to collect fresh data
3. Output is written to `data.json` for analysis or further processing
4. Use development tools (ruff, isort) to maintain code quality