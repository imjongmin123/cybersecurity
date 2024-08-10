import os
import re
import argparse
import requests
from urllib.parse import urljoin, urlparse, unquote
import html
import base64
import hashlib

VALID_IMAGE_EXTENSIONS = ['.png', '.jpeg', '.jpg', '.bmp', '.gif']

def download_image(url, folder):
    if url.startswith('data:image/'):
        mime_type, base64_data = url.split(',', 1)
        file_extension = mime_type.split('/')[1].split(';')[0]

        if f'.{file_extension}' not in VALID_IMAGE_EXTENSIONS:
            print(f"Skipping unsupported data URL with extension: {file_extension}")
            return

        img_name = f'data_image.{file_extension}'

        img_data = base64.b64decode(base64_data)
        img_path = os.path.join(folder, img_name)
        
        with open(img_path, 'wb') as f:
            f.write(img_data)
        print(f"Downloaded {img_name} from data URL")
        return
    
    response = requests.get(url)
    if response.status_code == 200:
        file_extension = os.path.splitext(urlparse(url).path)[1].lower()
        
        if file_extension not in VALID_IMAGE_EXTENSIONS:
            print(f"Skipping unsupported URL with extension: {file_extension}")
            return
        
        img_name = hashlib.md5(url.encode('utf-8')).hexdigest() + file_extension
        img_name = unquote(img_name) 
        if not img_name:
            img_name = 'default_image.jpg'
        img_path = os.path.join(folder, img_name)
        with open(img_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {img_name}")

def find_images(html_content, base_url):
	img_tags = re.findall(r'<img[^>]+src="([^">]+)"', html_content)
	img_urls = [urljoin(base_url, img_url.replace('\\/', '/')) for img_url in img_tags]

	json_img_urls = re.findall(r'"url":"(https[^"]+)"', html_content)
	json_img_urls = [html.unescape(url.replace('\\/', '/')) for url in json_img_urls]

	valid_img_urls = [url for url in img_urls + json_img_urls if os.path.splitext(urlparse(url).path)[1].lower() in VALID_IMAGE_EXTENSIONS]

	return valid_img_urls

def find_links(html_content, base_url):
    link_tags = re.findall(r'<a[^>]+href="([^">]+)"', html_content)
    link_urls = [urljoin(base_url, link_url.replace('\\/', '/')) for link_url in link_tags]
    return link_urls

def get_html_content(url, headers):
    response = requests.get(url, headers=headers)
    html_text = response.text
    decoded_html_text = html.unescape(html_text)
    return decoded_html_text


def download_images_from_url(url, folder, depth):
	if depth <= 0:
		return

	if not os.path.exists(folder):
		os.makedirs(folder)

	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
	}
	html_content = get_html_content(url, headers)
	if not html_content:
		print(f"Failed to retrieve or decode content from {url}")
		return
	img_urls = find_images(html_content, url)
	for img_url in img_urls:
		download_image(img_url, folder)

	if depth > 1:
		link_urls = find_links(html_content, url)
		for link_url in link_urls:
			download_images_from_url(link_url, folder, depth - 1)

def main():
	parser = argparse.ArgumentParser(description='Website images scraper')
	parser.add_argument('-r', '--recursive', action='store_true')
	parser.add_argument('-l', '--depth', type=int, default=1)
	parser.add_argument('-p', '--path', default="./down_image", type=str)
	parser.add_argument('url', type=str)
	args = parser.parse_args()

	download_images_from_url(args.url, args.path, args.depth if args.recursive else 1)

if __name__ == "__main__":
    main()
