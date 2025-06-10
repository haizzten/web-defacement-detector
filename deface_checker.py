import datetime
import os
import time
import joblib
import requests
import warnings
from datetime import datetime
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import smtplib
from email.message import EmailMessage
import re
from urllib.parse import urlparse, unquote

# Config
smtp_server = 'smtp.gmail.com'
smtp_port = 587
sender_email = 'haizzzten@gmail.com'
sender_password = 'dsbn uzne wekb jirb'
receiver_email = '24550022@gm.uit.edu.vn'
model_dir="./model"
vectorizer_name="tfidf_vectorizer.joblib"
xgb_model_name="model_xgboost.joblib"
rf_model_name="model_random_forest.joblib"
ltgbm_model_name="model_lightgbm.joblib"
xt_model_name="model_extra_trees.joblib"

# Preprocessing function
def clean_text(text):
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'[^\w\s]', '', text)  # Remove all punctuation
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    return text

# Extract text from HTML content
def extract_text_from_html(html_content):
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract <body>
    body_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ""

    # Extract <title>
    if not body_text:
        title = soup.title.get_text(separator=' ', strip=True) if soup.title else ""
        body_text = title

    # Extract main content (e.g., <article>, <section>, <p>, <h1>, <h2>, <h3>)
    if not body_text:
        paragraphs = soup.find_all(['article', 'section', 'p', 'h1', 'h2', 'h3'])
        if paragraphs:
            body_text = ' '.join([p.get_text(separator=' ', strip=True) for p in paragraphs])

    # Extract <header>, <footer> if necessary
    if not body_text:
        header_footer = soup.find_all(['header', 'footer'])
        if header_footer:
            body_text = ' '.join([hf.get_text(separator=' ', strip=True) for hf in header_footer])

    # Extract <meta name="description">
    if not body_text:
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            body_text = meta_desc['content']

    # Extract <main>
    if not body_text:
        main_content = soup.find('main')
        if main_content:
            body_text = main_content.get_text(separator=' ', strip=True)

    # Extract others if nothing is found
    if not body_text:
        body_text = soup.get_text(separator=' ', strip=True)

    return clean_text(body_text)

def preprocess_text(text):
    text = text.lower()  # Convert all to lowercase
    text = re.sub(r'[^\w\s]', '', text)  # Remove all punctuation
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    return text

def ensure_https(url):
    # Remove spaces and decode encoded spaces
    url = unquote(url).strip()  # Decode '%20' into actual spaces and remove unnecessary spaces
    parsed_url = urlparse(url)

    if not parsed_url.scheme:
        url = "https://" + url
    return url

def get_links_from_homepage(base_url, valid_url = ''):  # Placeholder for actual links
    if valid_url == '':
        valid_url = base_url

    # print(f"\033[32mLink gotten from base url: {repr(base_url)}\033[0m")

    try:
        resp = requests.get(base_url, allow_redirects=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        links = set()

        invalid_ext_pattern = re.compile(r'\.(php|png|jpg|jpeg|gif|bmp|svg|html|asp|aspx|exe)(\?|$)', re.IGNORECASE)
        for a in soup.find_all('a', href=True):
            print(f"Found link >> {a} from {base_url}")
            href = a['href']
            # print(f"\033[32mLink gotten href: {repr(href)}\033[0m")
            # href = href.replace(valid_url, base_url)
            href = href.replace("http://localhost", base_url.rstrip('/'))
            if href.startswith(base_url):  # only include internal links
                if not invalid_ext_pattern.search(href):  # skip links with unwanted extensions
                    links.add(href)
        return list(links)
    except Exception as e:
        print(f"Error when fetching links: {e}")
        return []

# Load page và save HTML
def download_page(url):
    try:
        print(f"Downloading page: {url}")
        response = requests.get(url, verify=False, allow_redirects=False,timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error when dowwloading page {url}: {e}")
        return None

def send_alert(url):
    msg = EmailMessage()
    msg.set_content(f"⚠️ ALERT: Your site ({url}) appears to be defaced !!!")
    msg['Subject'] = '🚨 Defacement Detected!'
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
            print(f"⚠️ Sent alert for {url}")
    except Exception as e:
        print(f"Error sending email: {e}")

def is_valid_html(link):
    try:
        response = requests.head(link, timeout=5, allow_redirects=True)
        content_type = response.headers.get("Content-Type", "").lower()
        return "html" in content_type  # chỉ tiếp tục nếu là HTML
    except:
        return False  # lỗi thì bỏ qua luôn

def main():
    while True:
        # Get check values from environment variable or use default
        checking_interval = int(os.getenv('CHECKING_INTERVAL', 600))
        throttle_time = int(os.getenv('THROTTLE_TIME', 1))
        base_site = os.getenv('DEFACEMENT_CHECKED_SITE', 'http://wordpress:80/')
        # base_site = 'http://127.0.0.1:80/'  # Default value for testing
        # base_site = ensure_https(base_site)
        print(f"\033[33mLink gotten from Env: {repr(base_site)}\033[0m")
        
        for _ in range (10):
            try:
                requests.get(base_site, allow_redirects=False, timeout=5)
                break # out of retry loop if successful
            except requests.ConnectionError:
                print(f"\033[33mWaiting for {base_site} to be available...\033[0m")
                time.sleep(5)
        
        links = get_links_from_homepage(base_site)
        for link in links:
            print(f">> Checking link: {link}")
            if not is_valid_html(link):
                print(f"\033[33mSkipping {link} (Non-HTML content)\033[0m")
                continue
            html_content = download_page(link)
            if html_content:
                body_text = extract_text_from_html(html_content)
                preprocessed_text = preprocess_text(body_text)
                
                vectorizer = joblib.load(os.path.join(model_dir, vectorizer_name))
                xgb_model = joblib.load(os.path.join(model_dir, xgb_model_name))
                rf_model = joblib.load(os.path.join(model_dir, rf_model_name))

                tfidf_vector = vectorizer.transform([preprocessed_text])
                prediction = xgb_model.predict(tfidf_vector) and rf_model.predict(tfidf_vector)
                if prediction[0] == 1:
                    print(f"\033[31m{link} is defaced.\033[0m")
                    send_alert(link)
                    time.sleep(throttle_time) # Throttle to avoid email spamming
                else:
                    print(f"\033[32m{link} is safe.\033[0m")
        time.sleep(checking_interval)

if __name__ == "__main__":
    main()
