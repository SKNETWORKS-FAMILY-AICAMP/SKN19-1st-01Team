# kia_ev_faq_scraper.py
# Kia EV "전기차 FAQ" 7문항 -> JSON 저장
# - 대상: https://www.kia.com/kr/vehicles/kia-ev/guide/faq
# - "전기차 FAQ" 섹션만 골라 7개 수집
# - 답변의 원문 HTML(링크/이미지 포함)을 절대 URL로 치환하여 저장
# - 추출된 링크/이미지 목록도 별도로 저장
# - webdriver_manager 불필요 (Selenium Manager 사용)

import os
import re
import json
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


EV_FAQ_URL = "https://www.kia.com/kr/vehicles/kia-ev/guide/faq"

# 스크립트 파일 위치 기준 기본 출력 경로
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(SCRIPT_DIR, "data", "kia_ev_faq.json")


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
    # 간단 UA (특정 환경에서 도움될 수 있음)
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


# href/src/data-src/srcset 절대경로화 (정규식 기반)
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


def _extract_links_and_images(elem, base_url: str) -> (List[Dict[str, str]], List[Dict[str, str]]):
    """elem 하위에서 a[href], img를 추출(절대 URL 변환 포함)."""
    links: List[Dict[str, str]] = []
    images: List[Dict[str, str]] = []

    # a[href]
    try:
        for a in elem.find_elements(By.CSS_SELECTOR, "a[href]"):
            href = a.get_attribute("href") or ""
            text = (a.text or a.get_attribute("title") or "").strip() or href
            if href:
                links.append({"text": text, "href": href})
    except Exception:
        pass

    # img (src/data-src)
    try:
        for img in elem.find_elements(By.CSS_SELECTOR, "img"):
            src = img.get_attribute("src") or img.get_attribute("data-src") or ""
            alt = img.get_attribute("alt") or ""
            if src and not src.startswith(("http://", "https://", "data:")):
                src = urljoin(base_url, src)
            if src:
                images.append({"src": src, "alt": alt})
    except Exception:
        pass

    return links, images


def _extract_answer_from_panel(panel, base_url: str) -> Dict[str, Any]:
    """패널 요소로부터 텍스트/HTML/링크/이미지 추출."""
    answer_text = (panel.text or "").strip()
    try:
        raw_html = panel.get_attribute("innerHTML") or ""
    except Exception:
        raw_html = ""
    answer_html = _absolutize_urls_in_html(raw_html, base=base_url)
    links, images = _extract_links_and_images(panel, base_url)
    return {
        "answer_text": answer_text,
        "answer_html": answer_html,
        "links": links,
        "images": images,
    }


def _extract_answer(driver: webdriver.Chrome, btn, base_url: str, container=None) -> Dict[str, Any]:
    """질문 버튼/요약(버튼 또는 summary)을 클릭한 뒤 답변을 추출."""
    # 1) aria-controls 우선 (대부분 아코디언 구조)
    panel = None
    panel_id = btn.get_attribute("aria-controls")
    if panel_id:
        try:
            panel = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, panel_id))
            )
        except Exception:
            panel = None

    # 2) <summary> inside <details> 처리
    if panel is None:
        try:
            tag = (btn.tag_name or "").lower()
        except Exception:
            tag = ""
        if tag == "summary":
            try:
                panel = btn.find_element(By.XPATH, "./..")  # parent <details>
            except Exception:
                panel = None

    # 3) 버튼 부모의 다음 형제(많이 쓰는 패턴)
    if panel is None:
        try:
            parent = btn.find_element(By.XPATH, "./ancestor::*[1]")
            panel = parent.find_element(By.XPATH, ".//following-sibling::*[1]")
        except Exception:
            panel = None

    # 4) container 내부에서 '열린/활성' 영역(후보 중 텍스트 많은 것)
    if panel is None and container is not None:
        try:
            cands = container.find_elements(
                By.XPATH,
                ".//*[@role='region' or @aria-hidden='false' or contains(@class,'open') or contains(@class,'is-active')]"
            )
            panel = max(cands, key=lambda e: len(e.text or ""), default=None)
        except Exception:
            panel = None

    if panel is None:
        return {
            "answer_text": "",
            "answer_html": "",
            "links": [],
            "images": [],
        }

    return _extract_answer_from_panel(panel, base_url)


def _find_ev_faq_container(driver: webdriver.Chrome) -> Optional[webdriver.remote.webelement.WebElement]:
    """
    페이지에서 '전기차 FAQ' 섹션 컨테이너를 최대한 보수적으로 찾아 반환.
    - '전기차 FAQ' 텍스트가 들어간 제목/헤딩/탭/링크 근처의 최적 컨테이너 탐색
    """
    # 1) '전기차 FAQ' 텍스트 포함 요소 찾기 (헤딩/탭/버튼/링크 등)
    candidates = driver.find_elements(
        By.XPATH,
        "//*[contains(normalize-space(.), '전기차 FAQ')]"
    )
    # 스크롤해서 레이지로딩 유도
    if candidates:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", candidates[0])
        time.sleep(0.3)

    # 2) 각 후보 기준으로 근접 컨테이너 탐색
    for el in candidates:
        # (a) 가장 가까운 section/article/div 중, 버튼/summary가 다수 포함된 컨테이너를 선호
        try_paths = [
            "./ancestor::section[1]",
            "./ancestor::article[1]",
            "./ancestor::div[1]",
            "./ancestor::*[1]",
            "./following::*[1]",
            "./parent::*[1]",
        ]
        for xp in try_paths:
            try:
                cont = el.find_element(By.XPATH, xp)
            except Exception:
                cont = None
            if not cont:
                continue
            # 컨테이너에서 질문 버튼/summary가 3개 이상이면 유력
            try:
                btns = cont.find_elements(By.CSS_SELECTOR, "button[aria-controls]")
                if len(btns) < 3:
                    # details/summary도 고려
                    btns += cont.find_elements(By.CSS_SELECTOR, "details > summary")
            except Exception:
                btns = []
            if len(btns) >= 3:
                return cont

    # 3) 실패 시 대안: 페이지 내 아코디언/FAQ 섹션 추정
    fallbacks = driver.find_elements(
        By.CSS_SELECTOR,
        "section:has(button[aria-controls]), article:has(button[aria-controls]), div:has(button[aria-controls])"
    )
    if fallbacks:
        return fallbacks[0]

    return None


def scrape_kia_ev_faq(
    max_items: int = 7,
    url: str = EV_FAQ_URL,
    headless: bool = True
) -> List[Dict[str, Any]]:
    """
    Kia EV 가이드 페이지의 '전기차 FAQ' 섹션에서 상단부터 최대 max_items(기본 7개) 수집.
    """
    driver = _make_driver(headless=headless)
    results: List[Dict[str, Any]] = []
    try:
        driver.get(url)
        _try_close_any_modal(driver)

        # 페이지 기본 로딩 대기
        time.sleep(0.8)
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(0.6)

        # "전기차 FAQ" 섹션 컨테이너 찾기
        container = _find_ev_faq_container(driver)
        if not container:
            # 혹시 첫 스크롤에서 못 찾았을 수 있으니 더 내려봄
            driver.execute_script("window.scrollTo(0, 1600);")
            time.sleep(0.8)
            container = _find_ev_faq_container(driver)

        if not container:
            # 최후: 페이지 전체에서 버튼/summary 취합 후 7개만 (안전망)
            scope = driver
        else:
            scope = container
            # 섹션을 화면 중앙으로
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", container)
                time.sleep(0.4)
            except Exception:
                pass

        # 질문 요소 수집 (우선순위: button[aria-controls] -> details>summary -> 기타)
        q_elems: List[Any] = scope.find_elements(By.CSS_SELECTOR, "button[aria-controls]")
        if not q_elems:
            q_elems = scope.find_elements(By.CSS_SELECTOR, "details > summary")
        if not q_elems:
            # 흔한 아코디언 헤더 백업
            q_elems = scope.find_elements(
                By.CSS_SELECTOR,
                ".accordion button, .accordion__item > button, .accordion__header button, .faq-list button"
            )

        # 텍스트 있는 것만
        q_elems = [e for e in q_elems if (e.text or "").strip()]
        seen_questions = set()

        for elem in q_elems:
            if len(results) >= max_items:
                break

            try:
                qtext = (elem.text or "").strip()
                if not qtext or qtext in seen_questions:
                    continue

                # 펼치기 (가려진 요소도 동작하도록 JS 클릭)
                driver.execute_script("arguments[0].click();", elem)
                time.sleep(0.3)

                ans = _extract_answer(driver, elem, base_url=url, container=container if container else driver)
                results.append({
                    "source_url": url,
                    "section": "전기차 FAQ",
                    "question": qtext,
                    **ans
                })
                seen_questions.add(qtext)

                # 접기(선택)
                try:
                    driver.execute_script("arguments[0].click();", elem)
                except Exception:
                    pass

            except Exception:
                continue

        # 혹시 7개 미만이면 더 찾아서 채우기(안전망)
        if len(results) < max_items and scope is not driver:
            more_scope = driver
            more_qs = more_scope.find_elements(By.CSS_SELECTOR, "button[aria-controls], details > summary")
            for elem in more_qs:
                if len(results) >= max_items:
                    break
                try:
                    qtext = (elem.text or "").strip()
                    if not qtext or qtext in seen_questions:
                        continue
                    driver.execute_script("arguments[0].click();", elem)
                    time.sleep(0.25)
                    ans = _extract_answer(driver, elem, base_url=url, container=more_scope)
                    results.append({
                        "source_url": url,
                        "section": "전기차 FAQ",
                        "question": qtext,
                        **ans
                    })
                    seen_questions.add(qtext)
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
    p = argparse.ArgumentParser(description="Kia EV '전기차 FAQ' 7개 크롤링 → JSON 저장")
    p.add_argument("--url", default=EV_FAQ_URL, help="대상 EV FAQ URL")
    p.add_argument("--max-items", type=int, default=7, help="가져올 질문 개수(기본 7)")
    p.add_argument("--out", default=DEFAULT_OUT, help="출력 JSON 경로 (기본: ./data/kia_ev_faq.json)")
    p.add_argument("--headful", action="store_true", help="브라우저 창 보이기(디버깅용)")
    args = p.parse_args()

    faqs = scrape_kia_ev_faq(
        max_items=args.max_items,
        url=args.url,
        headless=not args.headful
    )
    save_to_json(faqs, args.out)
    print(f"[OK] {len(faqs)}개 저장 → {args.out}")
