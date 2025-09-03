# renault_faq_scraper.py
# 르노 코리아 고객지원 FAQ(첫 페이지) -> JSON 저장
# - 답변의 원문 HTML(링크/이미지 포함)을 절대 URL로 치환하여 저장
# - 추출된 링크/이미지 목록도 별도로 저장
# - webdriver_manager 불필요 (Selenium Manager 사용)

import os
import re
import json
import time
from typing import Any, Dict, List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

FAQ_URL = "https://mall.renaultkoream.com/user/customer/faq.do"

# 스크립트 파일 위치 기준 기본 출력 경로
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(SCRIPT_DIR, "data", "renault_faq.json")


def _ensure_parent_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _make_driver(headless: bool = True) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,2200")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )

    service = Service()
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(30)
    return driver


def _try_close_any_modal(driver: webdriver.Chrome) -> None:
    """자주 보이는 모달/배너를 닫아본다(있을 때만)."""
    for kw in ["확인", "닫기", "동의", "알림닫기", "동의하고 계속"]:
        try:
            btn = WebDriverWait(driver, 1.5).until(
                EC.element_to_be_clickable((By.XPATH, f"//button[contains(., '{kw}')]"))
            )
            btn.click()
            time.sleep(0.2)
        except Exception:
            pass


def _absolutize_urls_in_html(html: str, base: str) -> str:
    """HTML 내 상대경로를 절대 URL로 변환. (기아 코드와 동일)"""
    def repl_href_src(m):
        attr, quote, url = m.groups()
        if url.startswith(("http://", "https://", "mallto:", "tel:", "data:")):
            return f'{attr}={quote}{url}{quote}'
        return f'{attr}={quote}{urljoin(base, url)}{quote}'

    _HREF_SRC_RE = re.compile(r'(href|src)\s*=\s*([\'"])(.+?)\2', re.IGNORECASE)
    html = _HREF_SRC_RE.sub(repl_href_src, html)
    return html


def _extract_answer(driver: webdriver.Chrome, q_element, base_url: str) -> Dict[str, Any]:
    """질문 클릭 후 답변의 text/html/링크/이미지 추출."""
    try:
        # 질문을 클릭하여 답변을 노출시킴
        driver.execute_script("arguments[0].click();", q_element)
        
        # 답변이 로드될 때까지 대기
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td.qna_answer"))
        )

        # 답변이 있는 tr 요소를 찾음 (sibling::tr[1] 사용)
        answer_tr = q_element.find_element(By.XPATH, "./ancestor::tr/following-sibling::tr")
        panel = answer_tr.find_element(By.CSS_SELECTOR, "td.qna_answer")
        
        # 답변 닫기 (다음 질문을 위해)
        driver.execute_script("arguments[0].click();", q_element)

    except Exception:
        panel = None

    answer_text = ""
    answer_html = ""
    links: List[Dict[str, str]] = []
    images: List[Dict[str, str]] = []

    if panel is not None:
        answer_text = (panel.text or "").strip()
        try:
            raw_html = panel.get_attribute("innerHTML") or ""
            answer_html = _absolutize_urls_in_html(raw_html, base=base_url)
        except Exception:
            raw_html = ""
        
        try:
            for a in panel.find_elements(By.CSS_SELECTOR, "a[href]"):
                href = a.get_attribute("href") or ""
                text = (a.text or a.get_attribute("title") or "").strip() or href
                if href:
                    links.append({"text": text, "href": href})
        except Exception:
            pass

        try:
            for img in panel.find_elements(By.CSS_SELECTOR, "img"):
                src = img.get_attribute("src") or img.get_attribute("data-src") or ""
                alt = img.get_attribute("alt") or ""
                if src and not src.startswith(("http://", "https://", "data:")):
                    src = urljoin(base_url, src)
                if src:
                    images.append({"src": src, "alt": alt})
        except Exception:
            pass

    return {
        "answer_text": answer_text,
        "answer_html": answer_html,
        "links": links,
        "images": images,
    }


def scrape_renault_faq_first_page(
    max_items: int = 20,
    url: str = FAQ_URL,
    headless: bool = True
) -> List[Dict[str, Any]]:
    """르노 코리아 FAQ '첫 페이지'의 질문/답변을 상단부터 최대 max_items개 수집."""
    driver = _make_driver(headless=headless)
    results: List[Dict[str, Any]] = []
    try:
        driver.get(url)
        _try_close_any_modal(driver)

        # FAQ 항목이 로드될 때까지 기다림 (주문 관련 탭이 기본으로 열려있음)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.table_default_faq tbody tr"))
            )
        except Exception:
            time.sleep(1.0)
        
        # 질문 버튼 후보 수집
        q_elements = driver.find_elements(By.CSS_SELECTOR, "table.table_default_faq tbody tr td.tit")
        
        seen_questions = set()
        for q_el in q_elements:
            if len(results) >= max_items:
                break
            try:
                question = (q_el.text or "").strip()
                if not question or question in seen_questions:
                    continue
                
                ans = _extract_answer(driver, q_el, base_url=url)
                
                results.append({
                    "source_url": url,
                    "category": "주문 관련", # 기본 카테고리로 설정
                    "question": question,
                    **ans
                })
                seen_questions.add(question)
                
            except Exception as e:
                print(f"⚠️ FAQ 항목 크롤링 중 오류 발생: {e}")
                continue
        
        return results

    finally:
        driver.quit()


def save_to_json(data: Any, out_path: str) -> None:
    _ensure_parent_dir(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="르노 코리아 FAQ 1페이지 크롤링 → JSON 저장")
    p.add_argument("--url", default=FAQ_URL, help="대상 FAQ URL")
    p.add_argument("--max-items", type=int, default=20, help="가져올 질문 개수")
    p.add_argument("--out", default=DEFAULT_OUT, help="출력 JSON 경로")
    p.add_argument("--headful", action="store_true", help="브라우저 창 보이기(디버깅용)")
    args = p.parse_args()

    faqs = scrape_renault_faq_first_page(
        max_items=args.max_items,
        url=args.url,
        headless=not args.headful
    )
    save_to_json(faqs, args.out)
    print(f"[OK] {len(faqs)}개 저장 → {args.out}")