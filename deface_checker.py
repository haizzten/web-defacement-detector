import datetime
import os
import time
import joblib
import requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage
import joblib
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, unquote

# Config
smtp_server = 'smtp.gmail.com'
smtp_port = 587
sender_email = 'haizzzten@gmail.com'
sender_password = 'dsbn uzne wekb jirb'
receiver_email = '24550017@gm.uit.edu.vn'
CHECK_INTERVAL = 60  # giây

model = joblib.load("./dockerImage/model/random_forest_model.pkl")
vectorizer = joblib.load("./dockerImage/model/tfidf_vectorizer.pkl")
# model = joblib.load("/app/model/random_forest_model.pkl")
# vectorizer = joblib.load("/app/model/tfidf_vectorizer.pkl")

def download_page(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error when downloading page {url}: {e}")
        return None

# Preprocessing function
def clean_text(text):
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'[^\w\s]', '', text)  # Remove all punctuation
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    return text

# Extract text from HTML content
def extract_text_from_html(html_content):
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


def get_links_from_homepage(base_url):
    try:
        resp = requests.get(base_url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith(base_url):  # chỉ lấy link nội bộ
                links.add(href)
        return list(links)
    except Exception as e:
        print(f"Error when fetching links: {e}")
        return []

# Reload page và save HTML
def download_page(url):
    try:
        print(f"Downloading page: {url}")
        response = requests.get(url, verify=False, timeout=10)
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
            print(f"Sent alert for {url}")
    except Exception as e:
        print(f"Error sending email: {e}")

def main():
    while True:
        site = os.getenv('DEFACEMENT_CHECKED_SITE', "http://localhost:8090")  # Get site URL from environment variable or use default
        check_interval = int(os.getenv('CHECK_INTERVAL', 600))  # Get check interval from environment variable or use default
        # links = get_links_from_homepage(site)
        links = ["http://localhost:8090/aula-f75/", "http://localhost:8090/edifier-m4/"]
        for link in links:
            print(f"{datetime.datetime.now()} >> Checking link: {link}")
            html_content = download_page(link)
            if html_content:
                body_text = extract_text_from_html(html_content)
                preprocessed_text = preprocess_text(body_text)
                
                tfidf_vector = vectorizer.transform([preprocessed_text])
                prediction = model.predict(tfidf_vector)
                
                if prediction[0] == 1:
                    send_alert(link)
                else:
                    print(f"{link} is not defaced.")
        for defaced_link in links:
            print(f"{datetime.datetime.now()} >> Checking defaced link: {defaced_link}")
            html_content = download_page(defaced_link)
            if html_content:
                body_text = extract_text_from_html(html_content)
                preprocessed_text = preprocess_text(body_text)
                
                tfidf_vector = vectorizer.transform([preprocessed_text])
                prediction = model.predict(tfidf_vector)
                
                if prediction[0] == 1:
                    send_alert(defaced_link)
                else:
                    print(f"{defaced_link} is not defaced.")
        time.sleep(check_interval)

if __name__ == "__main__":
    main()
