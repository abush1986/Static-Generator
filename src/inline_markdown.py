from textnode import TextNode, TextType, text_node_to_html_node
from htmlnode import HTMLNode, ParentNode, LeafNode
import re

def extract_markdown_images(text):
    pattern = r"!\[(.*?)\]\((.*?)\)"
    return re.findall(pattern, text)

def extract_markdown_links(text):
    pattern = r"(?<!!)\[(.*?)\]\((.*?)\)"
    return re.findall(pattern, text)

def split_nodes_delimiter(old_nodes, delimiter, text_type):
    new_nodes = []
    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue
        
        split_nodes = []
        sections = old_node.text.split(delimiter)
        
        # If the length is even, it means a delimiter was not closed
        if len(sections) % 2 == 0:
            raise ValueError(f"Invalid markdown: matching closing delimiter '{delimiter}' not found")
        
        for i in range(len(sections)):
            if sections[i] == "":
                continue
            if i % 2 == 0:
                split_nodes.append(TextNode(sections[i], TextType.TEXT))
            else:
                split_nodes.append(TextNode(sections[i], text_type))
        new_nodes.extend(split_nodes)
    return new_nodes

def split_nodes_image(old_nodes):
    new_nodes = []
    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue
        
        original_text = old_node.text
        images = extract_markdown_images(original_text)
        if len(images) == 0:
            new_nodes.append(old_node)
            continue
            
        for image in images:
            sections = original_text.split(f"![{image[0]}]({image[1]})", 1)
            if len(sections) != 2:
                raise ValueError("Invalid markdown, image section not closed")
            if sections[0] != "":
                new_nodes.append(TextNode(sections[0], TextType.TEXT))
            new_nodes.append(TextNode(image[0], TextType.IMAGE, image[1]))
            original_text = sections[1]
        
        if original_text != "":
            new_nodes.append(TextNode(original_text, TextType.TEXT))
            
    return new_nodes

def split_nodes_link(old_nodes):
    new_nodes = []
    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue
        
        original_text = old_node.text
        links = extract_markdown_links(original_text)
        if len(links) == 0:
            new_nodes.append(old_node)
            continue
            
        for link in links:
            sections = original_text.split(f"[{link[0]}]({link[1]})", 1)
            if len(sections) != 2:
                raise ValueError("Invalid markdown, link section not closed")
            if sections[0] != "":
                new_nodes.append(TextNode(sections[0], TextType.TEXT))
            new_nodes.append(TextNode(link[0], TextType.LINK, link[1]))
            original_text = sections[1]
            
        if original_text != "":
            new_nodes.append(TextNode(original_text, TextType.TEXT))
            
    return new_nodes

def text_to_textnodes(text):
    nodes = [TextNode(text, TextType.TEXT)]
    nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "_", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
    nodes = split_nodes_image(nodes)
    nodes = split_nodes_link(nodes)
    return nodes

def markdown_to_blocks(markdown):
    # Split by double newlines
    blocks = markdown.split("\n\n")
    filtered_blocks = []
    for block in blocks:
        # Strip leading/trailing whitespace
        block = block.strip()
        # Skip empty blocks
        if block == "":
            continue
        filtered_blocks.append(block)
    return filtered_blocks

from enum import Enum

class BlockType(Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    CODE = "code"
    QUOTE = "quote"
    UNORDERED_LIST = "unordered_list"
    ORDERED_LIST = "ordered_list"

def block_to_block_type(block):
    lines = block.split("\n")

    # Headings
    if block.startswith(("# ", "## ", "### ", "#### ", "##### ", "###### ")):
        return BlockType.HEADING

    # Code
    if len(lines) > 1 and block.startswith("```") and block.endswith("```"):
        return BlockType.CODE

    # Quote
    if block.startswith(">"):
        for line in lines:
            if not line.startswith(">"):
                return BlockType.PARAGRAPH
        return BlockType.QUOTE

    # Unordered List
    if block.startswith("- "):
        for line in lines:
            if not line.startswith("- "):
                return BlockType.PARAGRAPH
        return BlockType.UNORDERED_LIST

    # Ordered List
    if block.startswith("1. "):
        i = 1
        for line in lines:
            if not line.startswith(f"{i}. "):
                return BlockType.PARAGRAPH
            i += 1
        return BlockType.ORDERED_LIST

    return BlockType.PARAGRAPH

def text_to_children(text):
    text_nodes = text_to_textnodes(text)
    children = []
    for text_node in text_nodes:
        html_node = text_node_to_html_node(text_node)
        children.append(html_node)
    return children

def heading_to_html_node(block):
    level = 0
    while block.startswith("#"):
        level += 1
        block = block[1:]
    if level > 6:
        level = 6
    block = block.strip().replace("\n", " ")
    children = text_to_children(block)
    return ParentNode(f"h{level}", children)

def paragraph_to_html_node(block):
    block = block.replace("\n", " ")
    children = text_to_children(block)
    return ParentNode("p", children)

def code_to_html_node(block):
    block = block.strip("`").lstrip("\n")
    code_node = LeafNode("code", block)
    return ParentNode("pre", [code_node])

def quote_to_html_node(block):
    lines = block.split("\n")
    text = " ".join(line.lstrip(">").strip() for line in lines)
    children = text_to_children(text)
    return ParentNode("blockquote", children)

def ul_to_html_node(block):
    lines = block.split("\n")
    items = []
    for line in lines:
        line = line.lstrip("- ").strip()
        children = text_to_children(line)
        li = ParentNode("li", children)
        items.append(li)
    return ParentNode("ul", items)

def ol_to_html_node(block):
    lines = block.split("\n")
    items = []
    for line in lines:
        line = re.sub(r"^\d+\.\s*", "", line).strip()
        children = text_to_children(line)
        li = ParentNode("li", children)
        items.append(li)
    return ParentNode("ol", items)

def markdown_to_html_node(markdown):
    blocks = markdown_to_blocks(markdown)
    children = []
    for block in blocks:
        block_type = block_to_block_type(block)
        if block_type == BlockType.HEADING:
            node = heading_to_html_node(block)
        elif block_type == BlockType.PARAGRAPH:
            node = paragraph_to_html_node(block)
        elif block_type == BlockType.CODE:
            node = code_to_html_node(block)
        elif block_type == BlockType.QUOTE:
            node = quote_to_html_node(block)
        elif block_type == BlockType.UNORDERED_LIST:
            node = ul_to_html_node(block)
        elif block_type == BlockType.ORDERED_LIST:
            node = ol_to_html_node(block)
        else:
            node = paragraph_to_html_node(block)
        children.append(node)
    return ParentNode("div", children)

def extract_title(markdown):
    lines = markdown.split("\n")
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()
    raise Exception("No h1 header found")