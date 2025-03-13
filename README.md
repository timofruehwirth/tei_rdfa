# tei-rdfa

> [!NOTE]  
> :construction: under construction


`tei_rdfa()` is a dedicated function to extract RDF data that is embedded through RDFa in TEI-XML.

It is written to handle namespace definitions that are encoded in a natively TEI (Text Encoding Initiative) way by means of `<prefixDef>` within the `<encodingDesc>` node of the `<teiHeader>`.

It performs the following tasks:
- test filename extension (`.xml` or `.tei`)
- test file source (file path or URL)
- read XML file (from file path or URL)

It takes three parameters:
