# Web Scraping Tools Documentation

This directory contains the Sphinx-based documentation for the Web Scraping Tools project.

## Building the Documentation

### Prerequisites

Install the required packages:

```bash
pip install -r requirements.txt
```

### Build HTML Documentation

```bash
# On Linux/Mac
make html

# On Windows
make.bat html
```

The generated documentation will be available in the `build/html` directory.

## Documentation Structure

- `source/`: Contains the source files for the documentation
- `build/`: Contains the generated documentation
- `source/modules/`: Contains documentation for each module in the project

## Modules Documented

- Immobiliare: Real estate scraping tools for immobiliare.it
- eBay/Vinted: Product listing scraping for eBay and Vinted
- Browser Use: General browser automation utilities
- INPA: Tools for working with INPA data
- Movie Downloader: Movie information downloading tools
- Ryanair: Flight monitoring tools
- House Crawler: Browser extension for real estate listings
