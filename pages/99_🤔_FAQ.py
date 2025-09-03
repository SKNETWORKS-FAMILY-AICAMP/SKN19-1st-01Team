# pages/99_🤔_faq.py
import os
import sys
import streamlit as st

# 프로젝트 루트 경로를 sys.path에 추가하여 scraper 모듈 임포트 가능하게
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from scraper import scrape_kia_faq_first_page
except Exception as e:
    st.error(f"'scraper' 모듈을 불러오지 못했습니다: {e}\n"
             "프로젝트 루트에 scraper.py가 있는지, 파일명이 정확한지 확인해 주세요.")
    st.stop()


st.set_page_config(page_title="Kia FAQ 뷰어", layout="centered")
st.title("기아 FAQ (첫 페이지) 뷰어")
st.caption("출처: 기아 고객지원 FAQ 페이지")

# 옵션
col1, col2 = st.columns([1, 1])
with col1:
    max_items = st.number_input("가져올 질문 개수", min_value=1, max_value=50, value=20, step=1)
with col2:
    do_refresh = st.checkbox("강제 새로고침(캐시 무시)", value=False)

# 캐시: 10분
@st.cache_data(show_spinner=False, ttl=600)
def _load_faqs(_max_items: int):
    return scrape_kia_faq_first_page(max_items=_max_items)

with st.spinner("FAQ를 불러오는 중입니다..."):
    faqs = scrape_kia_faq_first_page(max_items=max_items) if do_refresh else _load_faqs(max_items)

if not faqs:
    st.error("FAQ를 불러오지 못했습니다. (사이트 구조 변경/네트워크/브라우저 실행 문제일 수 있어요)")
    st.stop()

st.success(f"총 {len(faqs)}개 로드 완료")

# 검색
keyword = st.text_input("질문/답변 검색(선택):", "")
filtered = [
    f for f in faqs
    if not keyword
    or keyword.lower() in f["question"].lower()
    or keyword.lower() in f["answer"].lower()
]

# 렌더
for i, item in enumerate(filtered, 1):
    with st.expander(f"{i}. {item['question']}"):
        st.write(item["answer"] or "(내용 없음)")
