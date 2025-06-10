import base64
import xml.etree.ElementTree as ET
import re
import argparse
from urllib.parse import quote

def parse_multipart_form_data(body):

    fields = []
    boundary_match = re.search(r'^--([-\w]+)', body, re.MULTILINE)
    if not boundary_match:
        return body 

    boundary = boundary_match.group(1)
    parts = body.split(f'--{boundary}')
    
    for part in parts:
        name_match = re.search(r'name="([^"]+)"', part)
        value_match = re.search(r'\r\n\r\n(.*)', part, re.DOTALL)
        if name_match and value_match:
            key = name_match.group(1).strip()
            value = value_match.group(1).strip().rstrip('--')
            fields.append(f"{quote(key)}={quote(value)}")
    
    return '&'.join(fields)

def main():
    parser = argparse.ArgumentParser(description="Convert BurpSuite XML to simplified request list.")
    parser.add_argument("input", help="Input XML file exported from BurpSuite")
    parser.add_argument("output", help="Output text file to save normalized requests")
    args = parser.parse_args()

    try:
        tree = ET.parse(args.input)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ Error reading XML file: {e}")
        return

    output_lines = []

    for issue in root.findall('issue'):
        host_elem = issue.find('host')
        request_elem = issue.find('./requestresponse/request')

        if host_elem is None or request_elem is None:
            continue

        host = host_elem.text.strip()
        method = request_elem.attrib.get('method', 'GET')
        base64_data = request_elem.text.strip()

        try:
            decoded_data = base64.b64decode(base64_data).decode('utf-8', errors='ignore')
        except Exception:
            continue

        first_line = decoded_data.splitlines()[0]
        request_match = re.match(r"(GET|POST) (.+?) HTTP", first_line)
        if request_match:
            method = request_match.group(1)
            raw_path = request_match.group(2)
        else:
            continue 

        full_url = f"{host}{raw_path}"

        post_data = ''
        if method.upper() == 'POST':
            split_data = decoded_data.split('\r\n\r\n', 1)
            if len(split_data) > 1:
                post_data = split_data[1].strip()
                if "Content-Disposition: form-data" in post_data:
                    post_data = parse_multipart_form_data(post_data)
                else:
                    post_data = quote(post_data)

        if method.upper() == 'POST' and post_data:
            line = f"[POST] {full_url} ({post_data})"
        elif method.upper() == 'GET':
            line = f"[GET] {full_url}"
        else:
            line = f"[{method.upper()}] {full_url}"

        output_lines.append(line)

    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            for line in output_lines:
                f.write(f"{line}\n")
        print(f"✅ Normalized output saved to {args.output}")
    except Exception as e:
        print(f"❌ Error saving output: {e}")
