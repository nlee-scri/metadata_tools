from glob import glob
import xml.etree.ElementTree as ET


def parse_element(element):
    """
    Recursively parses an XML element and its children into a dictionary.

    Args:
        element (xml.etree.ElementTree.Element): The XML element to parse.

    Returns:
        dict: A dictionary representation of the XML element, including its attributes,
              children, and text content.
    """
    parsed_dict = {}
    if element.attrib:
        parsed_dict.update(element.attrib)
    for child in element:
        child_dict = parse_element(child)
        if child.tag in parsed_dict:
            if not isinstance(parsed_dict[child.tag], list):
                parsed_dict[child.tag] = [parsed_dict[child.tag]]
            parsed_dict[child.tag].append(child_dict)
        else:
            parsed_dict[child.tag] = child_dict
    if element.text and element.text.strip():
        parsed_dict["text"] = element.text.strip()
    return parsed_dict


def parse_xml(xml_text: str) -> dict:
    """
    Parses an XML string into a dictionary.

    Args:
        xml_text (str): The XML string to parse.

    Returns:
        dict: A dictionary representation of the XML string, or None if parsing fails.
    """
    # xml_text = "<Root>" + xml_text + "</Root>"
    try:
        root = ET.fromstring(xml_text)
        parsed_dict = {root.tag: parse_element(root)}
        return parsed_dict
    except Exception as e:
        print(e)
        return None

def print_elements(element, level=0):
    indent = "  " * level
    print(f"{indent}{element.tag}: {element.attrib}")
    for child in element:
        print_elements(child, level + 1)

def recursive_find_with_path(element, tag, path=""):
    """
    Recursively searches for all occurrences of a specific tag in an XML element and its children,
    and returns the path to each found element.

    Args:
        element (xml.etree.ElementTree.Element): The XML element to search within.
        tag (str): The tag to search for.
        path (str): The current path to the element.

    Returns:
        list: A list of tuples, each containing the path and the found element.
    """
    
    found_elements = []
    current_path = f"{path}/{element.tag}"
    if element.tag == tag:
        found_elements.append((current_path, element))
    for child in element:
        found_elements.extend(recursive_find_with_path(child, tag, current_path))
    return found_elements

def recursive_search_for_tag_with_attribute(element, tag, attribute, value):
    """_summary_

    Args:
        element (_type_): _description_
        tag (_type_): _description_
        attribute (_type_): _description_
        value (_type_): _description_

    Returns:
        _type_: _description_
    """
    
    if isinstance(element, str):
        element = ET.fromstring(element)
    
    if element.tag == tag and element.attrib.get(attribute) == value:
        return element
    
    for child in element:
        result = recursive_search_for_tag_with_attribute(child, tag, attribute, value)
        if result is not None:
            return result
    return None
