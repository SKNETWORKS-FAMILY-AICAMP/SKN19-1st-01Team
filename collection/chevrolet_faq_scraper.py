import os
import json
import time
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

# --- 설정 ---
URL = 'https://www.chevrolet.co.kr/evlife/faq.gm?utm_source'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 저장 파일 명
OUT_PATH = os.path.join(SCRIPT_DIR, "..", "datasets", "faq", "chevrolet_ev_faq.json")


# --- 드라이버 설정 ---
def make_driver():
    """기본 크롬 드라이버 (Options 없이)."""
    service = Service()  # Selenium Manager가 드라이버 자동 관리
    driver = webdriver.Chrome(service=service)  # <- options 인자 없음
    driver.set_page_load_timeout(30)
    return driver


# --- 메인 스크래핑 로직 ---
def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    driver = make_driver()
    try:
        driver.get(URL)
        time.sleep(1.0)  # 간단 대기 (필요시 조정)

        # 특정 요소에 접근
        faq_titles = driver.find_elements(By.CSS_SELECTOR, 'a.question')
        faq_answers = driver.find_elements(By.CSS_SELECTOR, 'div.answer')

        n = min(len(faq_titles), len(faq_answers))
        data = []
        # 질문과 답변을 짝지어 저장합니다.
        for i in range(n):
            question_text = (faq_titles[i].text or "").strip()
            if not question_text:
                continue

            answer_html_raw = faq_answers[i].get_attribute('innerHTML') or ""
            
            # HTML 태그와 개행문자 등을 제거하고 공백을 정규화합니다.
            text_without_html = re.sub(r'<[^>]+>', '', answer_html_raw)
            cleaned_answer = re.sub(r'\s+', ' ', text_without_html).strip()
            
            data.append({
                "question": question_text,
                "answer": cleaned_answer,
            })

        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[OK] {n}개 저장 → {OUT_PATH}")

    finally:
        driver.quit()


# --- 스크립트 실행 ---
if __name__ == "__main__":
    main()
