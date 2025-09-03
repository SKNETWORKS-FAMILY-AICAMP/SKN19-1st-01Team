# scraper.py
# Kia FAQ 첫 페이지 스크래핑 (Selenium Manager 사용: webdriver_manager 불필요)
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

FAQ_URL = "https://www.kia.com/kr/customer-service/center/faq"


def _make_driver(headless: bool = True) -> webdriver.Chrome:
    opts = Options()
    if headless:
        # 최신 헤드리스 모드
        opts.add_argument("--headless=new")
    # 컨테이너/서버 환경에서 안정성 옵션
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,2000")
    # 가벼운 UA 지정 (특정 환경에서 봇 차단 회피에 도움이 될 수 있음)
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )

    # Selenium 4.x: Service() 만 주면 Selenium Manager가 드라이버 자동관리
    service = Service()
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(30)
    return driver


def _try_close_any_modal(driver: webdriver.Chrome) -> None:
    """간혹 뜨는 안내/동의/닫기 모달을 닫아본다(있을 때만)."""
    for kw in ["확인", "닫기", "동의", "알림닫기"]:
        try:
            btn = WebDriverWait(driver, 1.5).until(
                EC.element_to_be_clickable((By.XPATH, f"//button[contains(., '{kw}')]"))
            )
            btn.click()
            time.sleep(0.2)
        except Exception:
            pass


def _extract_answer_for_button(driver: webdriver.Chrome, btn) -> str:
    """질문 버튼을 클릭한 직후, 가능한 방식으로 답변 텍스트를 추출."""
    # 1) aria-controls 우선
    panel_id = btn.get_attribute("aria-controls")
    if panel_id:
        try:
            panel_el = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, panel_id))
            )
            text = (panel_el.text or "").strip()
            if text:
                return text
        except Exception:
            pass

    # 2) 버튼 주변(부모의 다음 형제 등)에서 흔한 패턴 탐색
    try:
        parent = btn.find_element(By.XPATH, "./ancestor::*[1]")
        # 바로 다음 형제 또는 그 하위의 단락/리스트/텍스트
        candidates = parent.find_elements(
            By.XPATH,
            ".//following-sibling::*[1] | .//following-sibling::*[1]//p | .//following-sibling::*[1]//li"
        )
        texts = [c.text.strip() for c in candidates if (c.text or "").strip()]
        if texts:
            return "\n".join(texts).strip()
    except Exception:
        pass

    # 3) 페이지 내 열린(확장된) 영역 유사 탐색
    try:
        expanded = driver.find_elements(
            By.XPATH,
            "//*[@role='region' or @aria-hidden='false' or contains(@class,'open') or contains(@class,'is-active')]"
        )
        texts = [e.text.strip() for e in expanded if (e.text or "").strip()]
        if texts:
            # 가장 내용이 많은 블록 선택
            return max(texts, key=len)
    except Exception:
        pass

    return ""


def scrape_kia_faq_first_page(max_items: int = 20, url: str = FAQ_URL) -> list[dict[str, str]]:
    """기아 FAQ '첫 페이지'의 질문/답변을 상단부터 최대 max_items개 수집."""
    driver = _make_driver(headless=True)
    faqs: list[dict[str, str]] = []

    try:
        driver.get(url)
        _try_close_any_modal(driver)

        # FAQ 영역 로딩 기다림(헤더의 'FAQ' 텍스트 등)
        try:
            WebDriverWait(driver, 12).until(
                EC.presence_of_all_elements_located((By.XPATH, "//*[contains(., 'FAQ')]"))
            )
        except Exception:
            # 꼭 실패일 필요는 없음(사이트 문구 변동 가능). 잠깐 대기 후 진행.
            time.sleep(1.0)

        # 레이지 로딩 방지용 스크롤
        driver.execute_script("window.scrollTo(0, 600);")
        time.sleep(0.5)

        # 질문 버튼 후보들 수집
        q_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-controls]")
        if not q_buttons:
            # 백업 셀렉터들(사이트 구조 변경 대비)
            q_buttons = driver.find_elements(
                By.CSS_SELECTOR,
                ".accordion button, .accordion__item > button, .accordion__header button, .faq-list button"
            )

        # 텍스트 있는 버튼만, 상단부터 max_items
        q_buttons = [b for b in q_buttons if (b.text or "").strip()]
        seen_q = set()
        collected = 0

        for btn in q_buttons:
            if collected >= max_items:
                break

            try:
                q_text = (btn.text or "").strip()
                if not q_text or q_text in seen_q:
                    continue

                # 펼치기(가려진 요소도 동작하도록 JS 클릭)
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.25)

                a_text = _extract_answer_for_button(driver, btn)
                if not a_text:
                    a_text = "(답변 텍스트를 찾지 못했습니다.)"

                faqs.append({"question": q_text, "answer": a_text})
                seen_q.add(q_text)
                collected += 1

                # 정리용으로 다시 접기 시도(선택)
                try:
                    driver.execute_script("arguments[0].click();", btn)
                except Exception:
                    pass

            except Exception:
                # 개별 항목 실패는 무시하고 계속
                continue

        return faqs

    finally:
        driver.quit()
