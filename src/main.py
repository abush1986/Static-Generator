import os
import sys
import shutil
from textnode import TextNode, TextType
from inline_markdown import markdown_to_html_node, extract_title

def copy_directory(src, dst):
    # Delete the destination directory if it exists
    if os.path.exists(dst):
        shutil.rmtree(dst)
    
    # Create the destination directory
    os.makedirs(dst, exist_ok=True)
    
    # Copy all contents recursively
    for item in os.listdir(src):
        src_path = os.path.join(src, item)
        dst_path = os.path.join(dst, item)
        
        if os.path.isfile(src_path):
            shutil.copy(src_path, dst_path)
            print(f"Copied file: {dst_path}")
        elif os.path.isdir(src_path):
            copy_directory(src_path, dst_path)

def generate_page(from_path, template_path, dest_path, basepath="/"):
    print(f"Generating page from {from_path} to {dest_path} using {template_path}")
    
    # Read markdown
    with open(from_path, 'r') as f:
        markdown = f.read()
    
    # Read template
    with open(template_path, 'r') as f:
        template = f.read()
    
    # Convert to HTML
    html_node = markdown_to_html_node(markdown)
    content_html = html_node.to_html()
    
    # Extract title
    title = extract_title(markdown)
    
    # Replace placeholders
    full_html = template.replace("{{ Title }}", title).replace("{{ Content }}", content_html)
    
    # Replace paths with basepath
    full_html = full_html.replace('href="/', f'href="{basepath}')
    full_html = full_html.replace('src="/', f'src="{basepath}')
    
    # Ensure dest directory exists
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    # Write to file
    with open(dest_path, 'w') as f:
        f.write(full_html)

def generate_pages_recursive(dir_path_content, template_path, dest_dir_path, basepath="/"):
    # Walk through the content directory
    for root, dirs, files in os.walk(dir_path_content):
        for file in files:
            if file.endswith(".md"):
                # Get the relative path from content directory
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, dir_path_content)
                
                # Replace .md with .html in the path
                rel_html_path = rel_path.replace(".md", ".html")
                
                # Create destination path
                dest_path = os.path.join(dest_dir_path, rel_html_path)
                
                # Generate the page
                generate_page(src_path, template_path, dest_path, basepath)

def main():
    # Get basepath from command line argument, default to /
    basepath = sys.argv[1] if len(sys.argv) > 1 else "/"
    
    # Copy static directory to docs
    copy_directory("static", "docs")
    
    # Generate pages recursively from content directory
    generate_pages_recursive("content", "template.html", "docs", basepath)
    
    print("Static site generation complete!")

if __name__ == "__main__":
    main()