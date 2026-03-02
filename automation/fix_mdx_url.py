import os
import re
import urllib.parse

mdx_path = 'data/blog/2026-03-02-briefing.mdx'
with open(mdx_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace src="/static/images/..." with URL-encoded versions
def encode_match(match):
    prefix = match.group(1)
    url_path = match.group(2)
    # URL encode the path, but keep the slashes
    encoded_url = urllib.parse.quote(url_path)
    # quote will encode slashes if we don't handle them. But quote(url_path) encodes slashes as well? 
    # Let's specify safe='/'
    encoded_url = urllib.parse.quote(url_path, safe='/')
    return f'{prefix}="{encoded_url}"'

new_content = re.sub(r'(<img[^>]*src)="(.*?)"', encode_match, content)

with open(mdx_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
    
print("Replaced encoded URLs.")
