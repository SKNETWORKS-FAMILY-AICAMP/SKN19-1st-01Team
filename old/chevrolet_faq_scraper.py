# -*- coding: utf-8 -*-
r"""
쉐보레 EV LIFE FAQ 스크레이퍼 (기아 예시 포맷으로 출력)
- 대상: https://www.chevrolet.co.kr/evlife/faq.gm
- 동작: Selenium 렌더링 → 아코디언 전개 → Q/A + links + images + answer_html 추출
- 출력(JSON 배열): C:/Users/Playdata/SKN19th/project1/SKN19-1st-4Team/data/chevrolet_ev_faq.json
"""

import sys
import re
import time
import json
from pathlib import Path
from typing import List, Dict, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ----------------------
# 설정
# ----------------------
TARGET_URL = "https://www.chevrolet.co.kr/evlife/faq.gm"
OUTPUT_DIR = Path(r"C:\Users\Playdata\SKN19th\project1\SKN19-1st-4Team\data")   # ← 사용자 지정 경로
OUTPUT_FILE = OUTPUT_DIR / "chevrolet_ev_faq.json"
RAW_HTML_DUMP = OUTPUT_DIR / "chevrolet_ev_faq_raw.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ----------------------
# 유틸
# ----------------------
def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def clean_text(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def dump_raw_html(html: str):
    try:
        ensure_dir(RAW_HTML_DUMP.parent)
        RAW_HTML_DUMP.write_text(html, encoding="utf-8")
    except Exception:
        pass

def get_soup(html: str) -> BeautifulSoup:
    """
    lxml이 없으면 내장 html.parser로 자동 폴백
    """
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")

def get_section_title_from_html(html: str) -> str:
    soup = get_soup(html)
    cand = soup.select_one("h1, .heading, .title, .page-title")
    if cand:
        t = clean_text(cand.get_text())
        if t:
            return t
    for sel in ["h2", "h3", "h4"]:
        for h in soup.select(sel):
            t = clean_text(h.get_text())
            if t and ("FAQ" in t or "Faq" in t or "faq" in t):
                return t
    return "EV LIFE FAQ"

def to_abs(url: str) -> str:
    return urljoin(TARGET_URL, url)

# ----------------------
# 정적 파싱 (백업용)
# ----------------------
def parse_static(html: str) -> List[Dict]:
    soup = get_soup(html)
    items: List[Dict] = []

    # (1) <dl><dt>Q</dt><dd>A</dd></dl> 패턴
    for dl in soup.select("dl"):
        dts = dl.find_all("dt")
        dds = dl.find_all("dd")
        for dt, dd in zip(dts, dds):
            q = clean_text(dt.get_text(" "))
            a_text = clean_text(dd.get_text(" "))
            if q and a_text:
                items.append({
                    "source_url": TARGET_URL,
                    "section": get_section_title_from_html(html),
                    "question": q,
                    "answer_text": a_text,
                    "answer_html": str(dd),
                    "links": [],
                    "images": []
                })

    # (2) 흔한 클래스 기반 (faq/accordion)
    if not items:
        for item in soup.select(
            '[class*="faq"] [class*="item"], [class*="accordion"] [class*="item"], '
            '[class*="faq-item"], [class*="accordion-item"]'
        ):
            q_node = (item.select_one(".question, .faq-question, [class*='question'], h3, h4")
                      or item.find(attrs={"role": "button"}))
            a_node = (item.select_one(".answer, .faq-answer, [class*='answer'], .accordion-body, [role='region']")
                      or item.find("p"))
            if not q_node or not a_node:
                continue
            q = clean_text(q_node.get_text(" "))
            a_text = clean_text(a_node.get_text(" "))
            if not (q and a_text):
                continue
            items.append({
                "source_url": TARGET_URL,
                "section": get_section_title_from_html(html),
                "question": q,
                "answer_text": a_text,
                "answer_html": str(a_node),
                "links": [],
                "images": []
            })

    return items

# ----------------------
# 동적 렌더링 (Selenium Manager 사용)
# ----------------------
def render_and_collect(url: str, wait_sec: int = 12) -> Tuple[str, List[Dict]]:
    """
    Selenium으로 페이지 렌더링 → 모든 질문(아코디언 헤더) 전개 → 인접/연결된 패널에서 A 추출
    Selenium Manager 사용: webdriver-manager 설치 불필요
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1440,1200")
    opts.add_argument("--lang=ko-KR")

    service = Service()  # Selenium Manager가 드라이버 자동 관리
    driver = webdriver.Chrome(service=service, options=opts)

    try:
        driver.get(url)
        WebDriverWait(driver, wait_sec).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # 팝업/배너 닫기 시도
        for label in ["동의", "수락", "확인", "Accept", "agree"]:
            try:
                for b in driver.find_elements(By.XPATH, f"//button[contains(., '{label}')]"):
                    if b.is_displayed():
                        driver.execute_script("arguments[0].click();", b)
                        time.sleep(0.3)
            except Exception:
                pass

        # 지연 로드 대비 스크롤
        last_h = 0
        for _ in range(8):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.7)
            h = driver.execute_script("return document.body.scrollHeight")
            if h == last_h:
                break
            last_h = h

        # "모두 펼치기" 류 버튼 먼저 시도
        for label in ["모두 펼치기", "전체 펼치기", "전체보기", "더 보기", "더보기", "전체 열기"]:
            try:
                btns = driver.find_elements(By.XPATH, f"//button[contains(., '{label}')]")
                for b in btns:
                    if b.is_displayed():
                        driver.execute_script("arguments[0].click();", b)
                        time.sleep(0.4)
            except Exception:
                pass

        # 질문(아코디언 헤더) 후보 수집
        q_xpaths = [
            "//button[@aria-controls]",
            "//button[@aria-expanded]",
            "//details/summary",
            "//*[contains(@class,'accordion')]//button",
            "//*[contains(@class,'faq')]//button",
            "//h3[ancestor::*[contains(@class,'accordion') or contains(@class,'faq')]]",
            "//h4[ancestor::*[contains(@class,'accordion') or contains(@class,'faq')]]",
        ]
        q_elems = []
        for xp in q_xpaths:
            try:
                q_elems.extend(driver.find_elements(By.XPATH, xp))
            except Exception:
                pass

        # 중복 제거
        seen = set(); uniq_qs = []
        for el in q_elems:
            try:
                key = (el.tag_name, (el.get_attribute("outerHTML") or "")[:200])
                if key not in seen:
                    seen.add(key); uniq_qs.append(el)
            except Exception:
                continue

        def extract_panel(el):
            panel = None
            # aria-controls
            try:
                ctrl = el.get_attribute("aria-controls")
                if ctrl:
                    try:
                        panel = driver.find_element(By.ID, ctrl)
                    except Exception:
                        panel = None
            except Exception:
                pass
            # details/summary
            if panel is None:
                try:
                    if el.tag_name.lower() == "summary":
                        parent = el.find_element(By.XPATH, "./..")
                        sibs = parent.find_elements(By.XPATH, "./*")
                        for s in sibs:
                            if s.tag_name.lower() != "summary":
                                panel = s; break
                except Exception:
                    pass
            # 다음 형제
            if panel is None:
                try:
                    sib = el
                    for _ in range(6):
                        sib = sib.find_element(By.XPATH, "following-sibling::*[1]")
                        if sib and sib.is_displayed() and clean_text(sib.text):
                            panel = sib; break
                except Exception:
                    pass
            # 상위 컨테이너에서 answer 유사 클래스
            if panel is None:
                try:
                    container = el.find_element(By.XPATH, "./ancestor::*[contains(@class,'item') or contains(@class,'accordion')][1]")
                except Exception:
                    try:
                        container = el.find_element(By.XPATH, "./ancestor::*[1]")
                    except Exception:
                        container = None
                if container is not None:
                    try:
                        cand = container.find_element(
                            By.XPATH,
                            ".//*[contains(@class,'answer') or contains(@class,'panel') or "
                            "contains(@class,'accordion-body') or contains(@class,'content') or "
                            "contains(@role,'region')]"
                        )
                        if cand and clean_text(cand.text):
                            panel = cand
                    except Exception:
                        pass
            return panel

        items: List[Dict] = []
        for el in uniq_qs:
            try:
                q_txt = clean_text(el.text or el.get_attribute("textContent") or "")
                if not q_txt or len(q_txt) < 2:
                    continue
                # 펼치기
                try:
                    expanded = el.get_attribute("aria-expanded")
                    if expanded is None or expanded == "false":
                        driver.execute_script("arguments[0].click();", el)
                        time.sleep(0.25)
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", el)
                        time.sleep(0.25)
                    except Exception:
                        pass

                panel = extract_panel(el)
                if not panel:
                    continue

                a_text = clean_text(panel.text or "")
                a_html = panel.get_attribute("innerHTML") or ""
                if not a_text and not a_html:
                    continue

                # 링크/이미지
                links, images = [], []
                try:
                    for a in panel.find_elements(By.TAG_NAME, "a"):
                        href = a.get_attribute("href")
                        text = clean_text(a.text or a.get_attribute("aria-label") or "")
                        if href:
                            links.append({"text": text, "href": to_abs(href)})
                except Exception:
                    pass
                try:
                    for im in panel.find_elements(By.TAG_NAME, "img"):
                        src = im.get_attribute("src"); alt = im.get_attribute("alt") or ""
                        if src:
                            images.append({"src": to_abs(src), "alt": alt})
                except Exception:
                    pass

                items.append({
                    "source_url": TARGET_URL,
                    "section": "",  # 후단에서 채움
                    "question": q_txt,
                    "answer_text": a_text,
                    "answer_html": a_html,
                    "links": links,
                    "images": images
                })
            except Exception:
                continue

        html = driver.page_source
        section = get_section_title_from_html(html)
        for it in items:
            if not it["section"]:
                it["section"] = section

        return html, items

    finally:
        try:
            driver.quit()
        except Exception:
            pass

# ----------------------
# 메인 로직
# ----------------------
def scrape() -> List[Dict]:
    # 1) 동적 렌더링 우선
    try:
        html, items = render_and_collect(TARGET_URL)
        if items:
            return items
        dump_raw_html(html)  # 무결과면 원본 저장
    except Exception as e:
        print(f"[Selenium 실패] {type(e).__name__}: {e}", file=sys.stderr)

    # 2) 정적 백업
    try:
        r = requests.get(TARGET_URL, headers=HEADERS, timeout=20)
        r.raise_for_status()
        html = r.text
        items = parse_static(html)
        if not items:
            dump_raw_html(html)
        return items
    except Exception as e:
        print(f"[정적 요청 실패] {type(e).__name__}: {e}", file=sys.stderr)
        return []

def main():
    ensure_dir(OUTPUT_DIR)
    items = scrape()

    # 기아 예시처럼 "배열"로 저장
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"[완료] FAQ {len(items)}건 저장 -> {OUTPUT_FILE}")
    if not items:
        print(f"[참고] FAQ가 비어 있습니다. 원본 HTML 덤프: {RAW_HTML_DUMP}")

if __name__ == "__main__":
    main()
