# import

import os  # import os module for interacting with operating system
import urllib.request  # import ulrlib.request module for fetching data from URLs
import logging  # import logging module for tracking events
from typing import Dict, Optional, Union, List, Tuple  # import type annotations for hinting types
from collections import defaultdict  # import defaultdict class with default values for missing keys
from lxml import etree  # import etree module for handling XML data
from rdflib import Graph, URIRef, Literal, Namespace  # import core classes for working with RDF
from rdflib.namespace import DC, RDF, RDFS  # import predefined DC, RDF, and RDFS namespaces

# logger

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s\n')  # configure root logger for logging from info level up, define message format printf-style
logger = logging.getLogger(__name__)  # initiate logger instance specific to file/module


# tei_rdfa() function

def tei_rdfa(xmlfile: str, xpath_expr: Optional[str] = None, verbose: bool = True) -> Graph:  # define function
    '''
    extracts RDFa data from TEI-XML file into RDF graph
    
    has parameters:
    xmlfile (str): file path/URL to TEI-XML file with .xml or .tei extension
    xpath_expr (str, optional): XPath expression to target TEI-XML elements for RDFa parsing
    verbose (bool): boolean flag to control printing serialized graphs
    
    returns:
    rdflib.Graph: RDF graph containing extracted triples
    '''
    
    # check filename extension

    file_lower = xmlfile.lower()  # render filename lowercase
    if not (file_lower.endswith('.xml') or file_lower.endswith('.tei')):  # check filename extension
        raise ValueError('Invalid file format: filename must have .xml or .tei extension.')  # raise exception

    # load XML file

    try:
        tree, xml_source = load_xml_file(xmlfile)  # call load_xml_file() helper function, store parsed XML tree and source in variables
            
        # provide feedback
        root = tree.getroot()  # retrieve XML root element
        if verbose:  # check verbosity parameter
            child_elements = ', '.join(element.tag for element in root)  # join list of direct child elements into string
            logger.info(f'Loading {xmlfile} ...\n'
                        f'      XML root element: {root.tag}\n'
                        f'      direct child elements: {child_elements}')  # print feedback to console
            
        namespaces = {
            'tei': 'http://www.tei-c.org/ns/1.0',
            'xml': 'http://www.w3.org/XML/1998/namespace'
        }  # set up namespaces for XPath
        
        prefix_map = get_tei_prefixes(tree, namespaces)  # call get_tei_prefixes() helper function, create dictionary of namespace prefixes and URIs
        
        # create RDF graph
        g = Graph(bind_namespaces="none")  # initialize empty RDF graph object, block automatic binding of prefixes (to avoid double binding)
        for prefix, uri in prefix_map.items():  # iterate through prefix-URI pairs
            g.bind(prefix, uri)  # bind prefix to URI for graph serialization
        
        # process RDFa information
        if xpath_expr is not None:
            process_xpath_elements(tree, g, xpath_expr, namespaces, prefix_map, verbose)  # call process_xpath_elements() helper function, find and process passed elements
        else:
            process_element(tree.getroot(), None, g, prefix_map)  # process entire XML tree starting from root
        
        # output graph
        if verbose:  # check verbosity status
            logger.info('Serializing RDF graph in Turtle format ...')
            print(g.serialize(format='turtle'))
            
            logger.info('Serializing RDF graph in RDF-XML format ...')
            print(g.serialize(format='xml'))
        
        return g  # return RDF graph for futher processing

    # catch exceptions and re-raise with expanded information  
    except ValueError as e:
        raise ValueError(f'Value error encountered: {e}')  
    except OSError as e:
        raise OSError(f'OS error encountered: {e}')  


# process_xpath_elements() helper function

def process_xpath_elements(tree: etree.ElementTree, graph: Graph, xpath_expr: str, 
                          namespaces: Dict[str, str], prefix_map: Dict[str, str], verbose: bool) -> None:  # define function
    '''
    finds and processes elements matching passed XPath expression
    
    has parameters:
    tree (etree.ElementTree): parsed XML tree
    graph (rdflib.Graph): graph to add triples to
    xpath_expr (str): XPath expression to select elements
    namespaces (dict): namespace mapping for XPath queries
    prefix_map (dict): mapping of namespeace prefixes to URIs
    verbose (bool): boolean flag to control printing detailed output
    '''
    try:
        xpath_compiled = etree.XPath(xpath_expr, namespaces=namespaces)  # compile XPath expression
        elements = xpath_compiled(tree)  # execute compiled XPath expression against XML tree to return list of elements
        
        # handle erroneous element targeting
        if not elements:
            error_msg = f'No elements matching XPath expression "{xpath_expr}" detected in the document.'
            if verbose:
                logger.error(error_msg)
            raise ValueError(error_msg)
        
        # log successful targeting
        if verbose:
            logger.info(f'{len(elements)} element(s) matching XPath expression "{xpath_expr}" ...')
        
        # extract RDFa for each matching element
        for element in elements:
            process_element(element, None, graph, prefix_map)  # call process_element() helper function, extract RDFa information and add to graph

    # catch XPath-expression errors        
    except etree.XPathError as e:
        error_msg = f'Invalid XPath expression: {e}'
        logger.error(error_msg)
        raise ValueError(error_msg)


# load_xml_file() helper function

def load_xml_file(xmlfile: str) -> Tuple[etree.ElementTree, str]:  # define function
    '''
    loads XML file from file path/URL
    
    has parameters:
    xmlfile (str): file path/URL to TEI-XML file with .xml or .tei extension
    
    returns:
    tuple: (ElementTree, source_uri)
    '''
    parser = etree.XMLParser(resolve_entities=False)  # create XML parser, introduce security settings
    
    if xmlfile.startswith(('http://', 'https://')):  # test URL
        with urllib.request.urlopen(xmlfile) as response:  # open URL
            xml_bytes = response.read()  # read XML file as bytes to avoid character encoding issues
            tree = etree.ElementTree(etree.fromstring(xml_bytes, parser))  # parse bytes into ElementTree
        xml_source = xmlfile  # store URL as XML source
    elif os.path.isfile(xmlfile):  # test file and path
        with open(xmlfile, 'rb') as f:  # open file in binary mode to avoid character encoding issues
            tree = etree.parse(f, parser)  # parse file into ElementTree
        xml_source = 'file://' + os.path.abspath(xmlfile)  # store file URI as XML source
    else:
        raise ValueError('Invalid file path or URL format.')  # raise exception
        
    return tree, xml_source  # return parsed XML tree and source


# get_tei_prefixes() helper function

def get_tei_prefixes(tree: etree.ElementTree, namespaces: Dict[str, str]) -> Dict[str, str]:  # define function
    '''
    extracts namespace prefixes from TEI listPrefixDef element
    
    has parameters:
    tree (etree.ElementTree): parsed XML tree
    namespaces (dict): namespace mapping for XPath queries
    
    returns:
    dict: mapping of prefixes to their full URIs
    '''
    prefix_map = defaultdict(str)  # create defaultdict object (returning empty strings for missing keys)
    
    prefix_xpath = etree.XPath('//tei:encodingDesc/tei:listPrefixDef/tei:prefixDef', namespaces=namespaces)  # compile XPath expression for TEI prefixDef element
    prefix_defs = prefix_xpath(tree)  # execute compiled XPath expression against XML tree to return list of prefixDef elements
    
    for prefix_def in prefix_defs:  # loop through prefixDef elements
        prefix = prefix_def.get('ident')  # get value of ident attribute
        # skip if no ident attribute
        if not prefix:
            continue
            
        replacement_pattern = prefix_def.get('replacementPattern')  # get value of replacementPattern attribute
        # skip if no replacementPattern attribute
        if not replacement_pattern:
            continue
            
        # handle replacement pattern formats
        if '$1' in replacement_pattern:
            base_uri = replacement_pattern.split('$1')[0]
        elif '{$1}' in replacement_pattern:
            base_uri = replacement_pattern.split('{$1}')[0]
        else:
            base_uri = replacement_pattern
            
        prefix_map[prefix] = base_uri  # assign base namespace URI to prefix in defaultdict object
    
    # check presence of custom namespaces, otherwise add predefined RDF namespaces to defaultdict object
    if 'dc' not in prefix_map:
        prefix_map['dc'] = str(DC)
    if 'rdf' not in prefix_map:
        prefix_map['rdf'] = str(RDF)
    if 'rdfs' not in prefix_map:
        prefix_map['rdfs'] = str(RDFS)
    
    return dict(prefix_map)  # convert defaultdict object to dictionary


# process_element() helper function

def process_element(element: etree.Element, parent_subject: Optional[str], 
                   graph: Graph, prefix_map: Dict[str, str]) -> Optional[str]:  # define function
    '''
    recursively processes elements for RDFa attributes
    
    has parameters:
    element (etree.Element): XML element to process
    parent_subject (str, optional): subject URI from parent element
    graph (rdflib.Graph): RDF graph to add triples to
    prefix_map (dict): mapping of prefixes to URIs
    
    Returns:
    str or None: The subject URI of this element
    '''
    current_subject = determine_subject(element, parent_subject, prefix_map)  # call determine_subject() helper function, return subject URI
    
    if current_subject:
        process_typeof(element, current_subject, graph, prefix_map)  # call process_typeof() helper function, add triples to RDF graph

        process_property(element, current_subject, graph, prefix_map)  # call process_property() helper function, add triples to RDF graph
        
        process_rel(element, current_subject, graph, prefix_map)  # call process_rel() helper function, add triples to RDF graph
        
        process_rev(element, current_subject, parent_subject, graph, prefix_map)  # call process_rev() helper function, add triples to RDF graph
    
    # recursively process descendant elements
    for child in element:
        process_element(child, current_subject, graph, prefix_map)
    
    return current_subject


# determine_subject() helper function

def determine_subject(element: etree.Element, parent_subject: Optional[str], 
                     prefix_map: Dict[str, str]) -> Optional[str]:  # define function
    '''
    determines subject
    
    has parameters:
    element (etree.Element): XML element
    parent_subject (str, optional): subject URI from parent element
    prefix_map (dict): mapping of prefixes to URIs
    
    returns:
    str or None: subject URI
    '''
    # check presence of "about" attribute
    if 'about' in element.attrib:
        return expand_uri(element.attrib['about'], prefix_map)  # call expand_uri() helper function, return full "about" URI

    # check presence of "resource" attribute (when no "rel"/"rev" attributes are present; do not use "resource" as subject if "property" attribute is present)
    if 'resource' in element.attrib and not ('property' in element.attrib) and not ('rel' in element.attrib or 'rev' in element.attrib):
        return expand_uri(element.attrib['resource'], prefix_map)  # call expand_uri() helper function, return full "resource" URI

    return parent_subject  # inherit subject from parent


# process_typeof() helper function

def process_typeof(element: etree.Element, subject: str, graph: Graph, prefix_map: Dict[str, str]) -> None:  # define function
    '''
    processes "typeof" attribute
    
    has parameters:
    element (etree.Element): XML element
    subject (str): subject URI
    graph (rdflib.Graph): RDF graph to add triples to
    prefix_map (dict): mapping of prefixes to URIs
    '''
    # check presence of "typeof" attribute
    if 'typeof' not in element.attrib:
        return
        
    types = element.attrib['typeof'].split()  # list multiple space-separated "typeof" value(s)
    for type_uri in types:  # iterate through "typeof" values
        expanded_type = expand_uri(type_uri, prefix_map)  # call expand_uri() helper function, return full "typeof" URI
        graph.add((URIRef(subject), RDF.type, URIRef(expanded_type)))  # add triple to RDF graph


# process_property() helper function

def process_property(element: etree.Element, subject: str, graph: Graph, prefix_map: Dict[str, str]) -> None:  # define function
    '''
    processes "property" attribute
    
    has parameters:
    element (etree.Element): XML element
    subject (str): subject URI
    graph (rdflib.Graph): RDF graph to add triples to
    prefix_map (dict): mapping of prefixes to URIs
    '''
    # check presence of "property" attribute
    if 'property' not in element.attrib:
        return
        
    properties = element.attrib['property'].split()  # list multiple space-separated "property" value(s)
    for prop in properties:  # iterate through "property" values
        expanded_prop = expand_uri(prop, prefix_map)  # call expand_uri() helper function, return full "property" URI

        # check presence of "resource" attribute
        if 'resource' in element.attrib:
            obj_uri = expand_uri(element.attrib['resource'], prefix_map)  # call expand_uri() helper function, return full "resource" URI
            graph.add((URIRef(subject), URIRef(expanded_prop), URIRef(obj_uri)))  # add triple to RDF graph, with "resource" URI as object
        else:
            obj_value = determine_property_object(element, prefix_map)  # only if no "resource" attribute present: call determine_property_object() helper function, return object value (or None)
            
            # handle objects with no value
            if obj_value is None:
                obj_value = Literal('')  # create empty literal for properties with no content (to preserve RDFa "property" relationships even for empty objects)
                
            graph.add((URIRef(subject), URIRef(expanded_prop), obj_value))  # add triples to RDF graph


# determin_property_object() helper function

def determine_property_object(element: etree.Element, prefix_map: Dict[str, str]) -> Optional[Union[URIRef, Literal]]:  # define function
    '''
    determines object for "property" attribute
    
    has parameters:
    element (etree.Element): XML element
    prefix_map (dict): mapping of prefixes to URIs
    
    returns:
    URIRef, Literal, or None: object value
    '''
    # check presence of "content" attribute
    if 'content' in element.attrib:
        return Literal(element.attrib['content'])  # return "content" value as Literal (including empty string)


    # get cleaned text content (to block XML comments)
    def get_clean_text(node):
        if node.tag is etree.Comment or isinstance(node, etree._Comment):  # apply two methods for robust detection of XML comment
            return ''  # skip XML comment
            
        # get text content if available
        text = ''
        if node.text:
            text = node.text.strip()
            
        return text


    # get element content
    elem_text = get_clean_text(element)

    # check presence of element content
    if elem_text:
        return Literal(elem_text)  # return element content as Literal
        
    # get element content in child elements
    text_parts = []
    for child in element:  # iterate through child elements
        child_text = get_clean_text(child)
        if child_text:
            text_parts.append(child_text)
    
    if text_parts:
        return Literal(' '.join(text_parts))  # join child-element contents, return as Literal
            
    return None


# process_rel() helper function

def process_rel(element: etree.Element, subject: str, graph: Graph, prefix_map: Dict[str, str]) -> None:  # define function
    '''
    processes "rel" attribute for RDF predicate
    
    has parameters:
    element (etree.Element): XML element
    subject (str): subject URI
    graph (rdflib.Graph): RDF graph to add triples to
    prefix_map (dict): mapping of prefixes to URIs
    '''
    # check presence of "rel" attribute
    if 'rel' not in element.attrib:
        return
        
    relations = element.attrib['rel'].split()  # list multiple space-separated "rel" value(s)
    
    # handle "resource" attribute in same element
    if 'resource' in element.attrib:
        obj_uri = expand_uri(element.attrib['resource'], prefix_map)  # call expand_uri() helper function, return full "resource" URI
        for rel in relations:  # iterate through "rel" values
            expanded_rel = expand_uri(rel, prefix_map)  # call expand_uri() helper function, return full "rel" URI
            graph.add((URIRef(subject), URIRef(expanded_rel), URIRef(obj_uri)))  # add triple to RDF graph
        return
        
    # handle "resource" attributes in descendant elements
    resource_xpath = etree.XPath('.//*[@resource]')  # compile XPath expression for lower-level elements with "resource" attributes
    resource_elems = resource_xpath(element)
    
    if resource_elems:
        for rel in relations:  # iterate through "rel" values
            expanded_rel = expand_uri(rel, prefix_map)  # call expand_uri() helper function, return full "rel" URI
            for resource_elem in resource_elems:  # iterate through lower-level elements with "resource" attributes
                obj_uri = expand_uri(resource_elem.get('resource'), prefix_map)  # call expand_uri() helper function, return full "resource" URI
                graph.add((URIRef(subject), URIRef(expanded_rel), URIRef(obj_uri)))  # add triple to RDF graph


# process_rev() helper function

def process_rev(element: etree.Element, subject: Optional[str], parent_subject: Optional[str], 
               graph: Graph, prefix_map: Dict[str, str]) -> None:  # define function
    '''
    processes "rev" attribute for modeling reverse-relation triples
    
    has parameters:
    element (etree.Element): XML element
    subject (str, optional): subject URI of element
    parent_subject (str, optional): subject URI of parent element
    graph (rdflib.Graph): RDF graph to add triples to
    prefix_map (dict): mapping of prefixes to URIs
    '''
    # check presence of "rev" and "resource" attributes
    if 'rev' not in element.attrib or 'resource' not in element.attrib:
        return
        
    revs = element.attrib['rev'].split()  # list multiple space-separated "rev" value(s)
    obj_uri = expand_uri(element.attrib['resource'], prefix_map)  # call expand_uri() helper function, return full "resource" URI
    subject_uri = subject or parent_subject  # use current element's subject URI if available or fall back to parent-element
    
    # check availability of subject URI
    if not subject_uri:
        return
        
    for rev in revs:  # iterate through "rev" values
        expanded_rev = expand_uri(rev, prefix_map)  # call expand_uri() helper function, return full "rev" URI
        graph.add((URIRef(obj_uri), URIRef(expanded_rev), URIRef(subject_uri)))  # add reverse-relations triple to RDF graph


# expand_uri() helper function

def expand_uri(uri_ref: str, prefix_map: Dict[str, str]) -> str:  # define function
    '''
    expands prefixed URI
    
    has parameters:
    uri_ref (str): URI reference
    prefix_map (dict): mapping of prefixes to URIs
    
    returns:
    str: expanded URI
    '''
    # handle prefixed URI
    if ':' in uri_ref:
        prefix, local = uri_ref.split(':', 1)  # split URI reference into prefix and local name
        if prefix in prefix_map:
            return prefix_map[prefix] + local  # concatenate base URI and local name
    
    return uri_ref  # handle unprefixed URI