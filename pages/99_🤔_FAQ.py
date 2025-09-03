# pages/99_🤔_faq.py
import os
import json
import streamlit as st

st.set_page_config(page_title="Kia FAQ JSON 뷰어", layout="centered")
st.title("기아 FAQ (JSON 로드) 뷰어")
st.caption("사전에 scraper.py로 JSON을 생성해 두세요.")

DEFAULT_JSON = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "kia_faq.json")

col1, col2 = st.columns([2,1])
with col1:
    json_path = st.text_input("JSON 파일 경로", value=DEFAULT_JSON)
with col2:
    max_show = st.number_input("표시 개수 제한", min_value=1, max_value=200, value=50, step=1)

uploaded = st.file_uploader("또는 JSON 파일 업로드", type=["json"], accept_multiple_files=False)

@st.cache_data(show_spinner=False)
def _load_json_from_path(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _load_data():
    if uploaded is not None:
        try:
            return json.load(uploaded)
        except Exception as e:
            st.error(f"업로드 JSON 파싱 실패: {e}")
            return []
    else:
        try:
            return _load_json_from_path(json_path)
        except FileNotFoundError:
            st.warning("JSON 파일을 찾을 수 없습니다. 경로를 확인하거나 파일을 업로드하세요.")
            return []
        except Exception as e:
            st.error(f"JSON 로드 실패: {e}")
            return []

data = _load_data()
if not data:
    st.stop()

st.success(f"총 {len(data)}개 항목 로드 완료")

# 검색
q = st.text_input("질문/답변에서 검색(선택):", "")
if q:
    q_low = q.lower()
    data = [
        item for item in data
        if q_low in (item.get("question","").lower())
        or q_low in (item.get("answer_text","").lower())
        or q_low in (item.get("answer_html","").lower())
    ]

st.write(f"표시할 항목: {min(len(data), max_show)}개")

# 렌더링 옵션
show_link_list = st.checkbox("추출된 링크 목록도 별도로 표시", value=True)
show_image_gallery = st.checkbox("추출된 이미지도 별도로 표시(HTML 렌더 외 추가)", value=False)

for i, item in enumerate(data[:max_show], start=1):
    question = item.get("question", "").strip()
    with st.expander(f"{i}. {question}" if question else f"{i}. (제목 없음)"):
        # 1) HTML 그대로 렌더 (링크/이미지 포함)
        html = item.get("answer_html", "").strip()
        if html:
            st.markdown(html, unsafe_allow_html=True)
        else:
            # 백업으로 텍스트 표시
            st.write(item.get("answer_text", "") or "(내용 없음)")

        # 2) 옵션: 링크 목록
        if show_link_list:
            links = item.get("links", [])
            if links:
                st.markdown("**추출된 링크**")
                for L in links:
                    text = L.get("text") or L.get("href") or ""
                    href = L.get("href") or ""
                    if href:
                        st.markdown(f"- [{text}]({href})")
            else:
                st.caption("추출된 링크 없음")

        # 3) 옵션: 이미지 갤러리 (HTML 렌더 외 추가로)
        if show_image_gallery:
            imgs = item.get("images", [])
            if imgs:
                st.markdown("**추출된 이미지**")
                for img in imgs:
                    src = img.get("src")
                    alt = img.get("alt") or ""
                    if src:
                        st.image(src, caption=alt, use_column_width=True)
            else:
                st.caption("추출된 이미지 없음")
