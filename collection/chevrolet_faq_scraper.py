import time
import json
import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from urllib.parse import urljoin

path = 'chromedriver.exe'
service = webdriver.chrome.service.Service(path)
driver = webdriver.Chrome(service=service)

# 특정 url 접근
url = 'https://www.chevrolet.co.kr/evlife/faq.gm?utm_source'
driver.get(url)
time.sleep(1)

# 특정 요소에 접근
faq_titles = driver.find_elements(By.CSS_SELECTOR, 'a.question')
faq_answers = driver.find_elements(By.CSS_SELECTOR, 'div.answer')

faq_data = []
# 질문과 답변을 짝지어 저장합니다.
for title, answer in zip(faq_titles, faq_answers):
    question_text = title.text
    if not question_text:
        continue

    answer_text = answer.get_attribute('textContent').strip()
    answer_html = answer.get_attribute('innerHTML').strip()
    
    # TODO: answer_html에서 링크와 이미지 파싱
    links = []
    images = []

    faq_data.append({
        "source_url": url,
        "section": "EV라이프 FAQ",
        "question": question_text,
        "answer_text": answer_text,
        "answer_html": answer_html,
        "links": links,
        "images": images,
    })

driver.quit()

# 파일 경로 설정
# os.path.dirname(__file__)는 현재 스크립트 파일의 디렉토리를 반환합니다.
# '..'를 사용하여 상위 디렉토리로 이동하고, datasets/faq 폴더로 경로를 설정합니다.
output_dir = os.path.join(os.path.dirname(__file__), '..', 'datasets', 'faq')
os.makedirs(output_dir, exist_ok=True) # 디렉토리가 없으면 생성
file_path = os.path.join(output_dir, 'chevrolet_ev_faq.json')


# JSON 파일로 저장
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(faq_data, f, ensure_ascii=False, indent=2)

print(f"데이터를 {file_path} 에 성공적으로 저장했습니다.")