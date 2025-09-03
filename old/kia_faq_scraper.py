# kia_faq_scraper.py
# 기아 고객지원 FAQ(첫 페이지) -> JSON 저장
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

FAQ_URL = "https://www.kia.com/kr/customer-service/center/faq"

# 스크립트 파일 위치 기준 기본 출력 경로
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(SCRIPT_DIR, "data", "kia_faq.json")


def _ensure_parent_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _make_driver(headless: bool = True) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")  # 최신 헤드리스
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,2200")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )

    # Selenium 4.x: Service()만 넘기면 Selenium Manager가 드라이버 자동관리
    service = Service()
    # 자동 다운로드가 정책상 막히면 아래처럼 수동 경로 지정:
    # service = Service(executable_path=r"C:\tools\chromedriver\chromedriver.exe")
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


# 단순 정규식으로 href/src/data-src/srcset 절대경로화
_HREF_SRC_RE = re.compile(r'(href|src)\s*=\s*([\'"])(.+?)\2', re.IGNORECASE)
_DATA_SRC_RE = re.compile(r'(data-src)\s*=\s*([\'"])(.+?)\2', re.IGNORECASE)
_SRCSET_RE   = re.compile(r'(srcset)\s*=\s*([\'"])(.+?)\2', re.IGNORECASE)

def _absolutize_urls_in_html(html: str, base: str) -> str:
    """HTML 내 상대경로를 절대 URL로 변환."""
    def repl_href_src(m):
        attr, quote, url = m.groups()
        if url.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
            return f'{attr}={quote}{url}{quote}'
        return f'{attr}={quote}{urljoin(base, url)}{quote}'

    def repl_data_src(m):
        attr, quote, url = m.groups()
        if url.startswith(("http://", "https://", "data:")):
            return f'{attr}={quote}{url}{quote}'
        return f'{attr}={quote}{urljoin(base, url)}{quote}'

    def repl_srcset(m):
        attr, quote, val = m.groups()
        parts = []
        for token in val.split(","):
            token = token.strip()
            if not token:
                continue
            sp = token.split()
            url = sp[0]
            rest = " ".join(sp[1:])
            if not url.startswith(("http://", "https://", "data:")):
                url = urljoin(base, url)
            parts.append(url + (f" {rest}" if rest else ""))
        return f'{attr}={quote}{", ".join(parts)}{quote}'

    html = _HREF_SRC_RE.sub(repl_href_src, html)
    html = _DATA_SRC_RE.sub(repl_data_src, html)
    html = _SRCSET_RE.sub(repl_srcset, html)
    return html


def _extract_answer(driver: webdriver.Chrome, btn, base_url: str) -> Dict[str, Any]:
    """질문 버튼 클릭 후 답변의 text/html/링크/이미지 추출."""
    panel = None
    # 1) aria-controls로 연결된 panel을 우선 찾음
    panel_id = btn.get_attribute("aria-controls")
    if panel_id:
        try:
            panel = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, panel_id))
            )
        except Exception:
            panel = None

    # 2) 못 찾으면 버튼 부모의 다음 형제
    if panel is None:
        try:
            parent = btn.find_element(By.XPATH, "./ancestor::*[1]")
            panel = parent.find_element(By.XPATH, ".//following-sibling::*[1]")
        except Exception:
            panel = None

    # 3) 또 못 찾으면 열린/활성화된 영역 후보 중 텍스트가 가장 많은 것
    if panel is None:
        try:
            cands = driver.find_elements(
                By.XPATH,
                "//*[@role='region' or @aria-hidden='false' or contains(@class,'open') or contains(@class,'is-active')]"
            )
            panel = max(cands, key=lambda e: len(e.text or ""), default=None)
        except Exception:
            panel = None

    answer_text = ""
    answer_html = ""
    links: List[Dict[str, str]] = []
    images: List[Dict[str, str]] = []

    if panel is not None:
        # 텍스트
        answer_text = (panel.text or "").strip()

        # 원문 HTML + 절대 URL 치환
        try:
            raw_html = panel.get_attribute("innerHTML") or ""
        except Exception:
            raw_html = ""
        answer_html = _absolutize_urls_in_html(raw_html, base=base_url)

        # a[href] 추출
        try:
            for a in panel.find_elements(By.CSS_SELECTOR, "a[href]"):
                href = a.get_attribute("href") or ""
                text = (a.text or a.get_attribute("title") or "").strip() or href
                if href:
                    links.append({"text": text, "href": href})
        except Exception:
            pass

        # img 추출 (src, data-src, alt)
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


def scrape_kia_faq_first_page(
    max_items: int = 20,
    url: str = FAQ_URL,
    headless: bool = True
) -> List[Dict[str, Any]]:
    """기아 FAQ '첫 페이지'의 질문/답변을 상단부터 최대 max_items개 수집."""
    driver = _make_driver(headless=headless)
    results: List[Dict[str, Any]] = []
    try:
        driver.get(url)
        _try_close_any_modal(driver)

        # 질문 버튼 로딩 대기
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[aria-controls]"))
            )
        except Exception:
            time.sleep(1.0)

        # 레이지 로딩 방지용 스크롤
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(0.6)

        # 질문 버튼 후보 수집
        q_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-controls]")
        if not q_buttons:
            q_buttons = driver.find_elements(
                By.CSS_SELECTOR,
                ".accordion button, .accordion__item > button, .accordion__header button, .faq-list button"
            )

        q_buttons = [b for b in q_buttons if (b.text or "").strip()]
        seen_questions = set()

        for btn in q_buttons:
            if len(results) >= max_items:
                break
            try:
                question = (btn.text or "").strip()
                if not question or question in seen_questions:
                    continue

                # 펼치기 (가려진 요소도 잘 동작하도록 JS 클릭)
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.3)

                ans = _extract_answer(driver, btn, base_url=url)
                results.append({
                    "source_url": url,
                    "question": question,
                    **ans
                })
                seen_questions.add(question)

                # 접기(선택)
                try:
                    driver.execute_script("arguments[0].click();", btn)
                except Exception:
                    pass

            except Exception:
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
    p = argparse.ArgumentParser(description="Kia FAQ 1페이지 크롤링 → JSON 저장")
    p.add_argument("--url", default=FAQ_URL, help="대상 FAQ URL")
    p.add_argument("--max-items", type=int, default=20, help="가져올 질문 개수")
    p.add_argument("--out", default=DEFAULT_OUT, help="출력 JSON 경로")
    p.add_argument("--headful", action="store_true", help="브라우저 창 보이기(디버깅용)")
    args = p.parse_args()

    faqs = scrape_kia_faq_first_page(
        max_items=args.max_items,
        url=args.url,
        headless=not args.headful
    )
    save_to_json(faqs, args.out)
    print(f"[OK] {len(faqs)}개 저장 → {args.out}")
