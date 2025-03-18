# tei-rdfa

> [!NOTE]  
> :construction: under construction


`tei_rdfa()` is a dedicated function to extract RDF data that is embedded through RDFa in TEI-XML.

`tei_rdfa()` handles namespace definitions that are encoded through natively TEI (Text Encoding Initiative) formatting within `<prefixDef>` elements inside the `<encodingDesc>` node of the `<teiHeader>`.

It performs the following tasks:
- test filename extension (`.xml` or `.tei`)
- test file source (file path or URL)
- read XML file (from file path or URL)
- log progress and issue warnings

It takes three parameters:
