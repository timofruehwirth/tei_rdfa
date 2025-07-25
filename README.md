[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15234344.svg)](https://doi.org/10.5281/zenodo.15234344) [![License: GPLv3](https://img.shields.io/badge/License-GPLv3-green.svg)](https://www.gnu.org/licenses/gpl-3.0) [![PyPi Version](https://img.shields.io/pypi/v/tei-rdfa.svg)](https://pypi.python.org/pypi/tei-rdfa/)

> [!IMPORTANT]
> tei-rdfa is currently in beta and welcomes feedback from early adopters.

# tei-rdfa

A Python utility for extracting RDFa data from TEI-XML documents.

![tei-rdfa](tei-rdfa.png)

## Overview

`tei_rdfa()` is a dedicated function that extracts RDFa (Resource Description Framework in Attributes) data embedded in TEI (Text Encoding Initiative) XML documents and converts it into a standard RDF graph. The function handles native TEI namespace formatting through `<prefixDef>` elements (`//tei:encodingDesc/tei:listPrefixDef/tei:prefixDef`).[^1]

The tei-rdfa utility is a streamlined extractor tool that prioritizes simplicity and TEI-specific functionality, being intended to enable TEI+RDFa parsing in the absence of namespace-prefix attribution through HTML5-style `prefix` or XHTML/XML-style `xmlns:` attributes. For other uses, the [pyRdfa](https://pypi.org/project/pyRdfa3/) distiller/parser library, which comprehensively implements the full RDFa specification, will be preferable.

## Features

- Loads TEI-XML files from local paths or URLs
- Processes RDFa attributes `about`, `typeof`, `property`, `rel`, `rev`, `resource`, `content`
- Extracts and resolves namespace prefixes from TEI-specific `<prefixDef>` elements
- Generates RDF triples from embedded RDFa information
- Provides targeted extraction via XPath expressions
- Returns an RDFlib Graph object for further processing or serialization
- Implements robust error handling and informative error messages
- Offers verbose mode with detailed logging

## Parameters

- `xmlfile` (str): File path or URL to a TEI-XML file (must have `.xml` or `.tei` extension)
- `xpath_expr` (str, optional): XPath expression to target specific elements for RDFa extraction; will otherwise target the XML root element
- `verbose` (bool, default=True): Controls logging output

## Dependencies

- [RDFlib](https://rdflib.readthedocs.io): Core RDF functionality
- [lxml](https://lxml.de/): XML processing and XPath support

## Implementation Details

The package includes several helper functions that handle specific aspects of RDFa extraction. It implements defensive programming practices with input validation and comprehensive error handling for common issues:

- Invalid file extensions
- Invalid XML syntax
- Invalid URLs or file paths
- Invalid XPath syntax
- Erroneous XPath queries

Error messages provide contextual information to facilitate debugging and resolution.

## Installation

```shell
pip install tei-rdfa
```

## Example Usage

```python
from tei_rdfa import tei_rdfa

# Basic usage
graph = tei_rdfa('path/to/document.xml')

# With XPath to target specific elements
graph = tei_rdfa(
    xmlfile='https://example.org/document.tei',
    xpath_expr='//tei:person[2]',
    verbose=True
)

# Process resulting graph
print(graph.serialize(format='turtle'))
```

## Directory Structure

```
tei_rdfa/
├── LICENSE
├── README.md
├── pyproject.toml
└── tei_rdfa/
    ├── __init__.py
    ├── requirements.txt
    └── ipynb/
        └── tei_rdfa.ipynb
```
The repository is organized as follows:

- **tei_rdfa/** contains project metadata and configuration
- **tei_rdfa/tei_rdfa/** contains the package implementation
- **tei_rdfa/tei_rdfa/ipynb/** contains a Jupyter notebook demonstrating usage examples and error scenarios

---
[^1]: See https://github.com/TEIC/TEI/issues/1860.
