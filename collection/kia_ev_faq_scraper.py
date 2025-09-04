import os
import json
import time
import re # Add re import for regex operations

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://www.kia.com/kr/vehicles/kia-ev/guide/faq"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH   = os.path.join(SCRIPT_DIR, "..", "datasets", "faq", "kia_ev_faq.json")


def make_driver():
    """기본 크롬 드라이버 (Options 없이)."""
    service = Service()
    driver = webdriver.Chrome(service=service)
    driver.set_page_load_timeout(30)
    return driver


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    driver = make_driver()
    try:
        driver.get(URL)
        time.sleep(1.0)

        # 질문/답변 요소가 로드될 때까지 기다림
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.cmp-accordion__title"))
        )
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.faqinner__wrap"))
        )

        # 고정 셀렉터로 질문/답변 수집
        q_elems = driver.find_elements(By.CSS_SELECTOR, "span.cmp-accordion__title")
        a_elems = driver.find_elements(By.CSS_SELECTOR, "div.faqinner__wrap")

        n = min(len(q_elems), len(a_elems))
        data = []
        for i in range(n):
            question = (q_elems[i].text or "").strip()
            answer_html_raw = a_elems[i].get_attribute("innerHTML") or ""
            
            # HTML 태그와 개행문자 등을 제거하고 공백 정규화
            text_without_html = re.sub(r'<[^>]+>', '', answer_html_raw)
            cleaned_answer = re.sub(r'\s+', ' ', text_without_html).strip()
            
            data.append({"question": question, "answer": cleaned_answer})

        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[OK] {n}개 저장 → {OUT_PATH}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
