import os
import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

URL = "https://www.kia.com/kr/vehicles/kia-ev/guide/faq"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH   = os.path.join(SCRIPT_DIR, "data", "kia_ev_faq_simple.json")


def make_driver():
    """기본 크롬 드라이버 (Options 없이)."""
    service = Service()  # Selenium Manager가 드라이버 자동 관리
    driver = webdriver.Chrome(service=service)  # <- options 인자 없음
    driver.set_page_load_timeout(30)
    return driver


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    driver = make_driver()
    try:
        driver.get(URL)
        time.sleep(1.0)  # 간단 대기 (필요시 조정)

        # 고정 셀렉터로 질문/답변 수집
        q_elems = driver.find_elements(By.CSS_SELECTOR, "span.cmp-accordion__title")
        a_elems = driver.find_elements(By.CSS_SELECTOR, "div.faqinner__wrap")

        n = min(len(q_elems), len(a_elems))
        data = []
        for i in range(n):
            question = (q_elems[i].text or "").strip()
            answer = a_elems[i].get_attribute("innerHTML") or ""
            data.append({"question": question, "answer": answer})

        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[OK] {n}개 저장 → {OUT_PATH}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
