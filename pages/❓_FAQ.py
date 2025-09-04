import streamlit as st
import pandas as pd
from connection import get_connection # DB 연결
import mysql.connector # 에러 핸들링용

st.set_page_config(page_title="EV FAQ 상세", layout="wide")
st.title("❓ EV FAQ 상세 조회")
st.caption("데이터베이스에서 FAQ 데이터를 불러와 검색 및 조회합니다.")

# --- DB에서 FAQ 데이터 로드 함수 ---
@st.cache_data(ttl=3600) # 1시간 캐시
def load_all_faqs_from_db():
    conn = None
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    m.name as manufacturer_name, 
                    faq.question, 
                    faq.answer
                FROM EV_Manufacturer_FAQ faq
                JOIN EV_Manufacturer m ON faq.manufacturer_id = m.id
                ORDER BY m.name, faq.question
            """)
            faqs_df = pd.DataFrame(cursor.fetchall())
            return faqs_df
    except mysql.connector.Error as err:
        st.error(f"FAQ 데이터 로드 중 오류 발생: {err}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# 데이터 로드
data_df = load_all_faqs_from_db()

if data_df.empty:
    st.warning("FAQ 데이터를 불러오지 못했습니다. DB 연결 및 테이블을 확인해주세요.")
    st.stop()

st.success(f"총 {len(data_df)}개 항목 로드 완료")

# 검색 필터
search_query = st.text_input("질문/답변에서 검색:", "")

filtered_df = data_df
if search_query:
    search_query_lower = search_query.lower()
    filtered_df = data_df[
        data_df['question'].str.lower().str.contains(search_query_lower) |
        data_df['answer'].str.lower().str.contains(search_query_lower)
    ]

st.write(f"표시할 항목: {len(filtered_df)}개")

# 제조사별 필터 (선택 사항)
manufacturers = ['전체'] + list(data_df['manufacturer_name'].unique())
selected_manufacturer = st.selectbox("제조사별 필터:", manufacturers)

if selected_manufacturer != '전체':
    filtered_df = filtered_df[filtered_df['manufacturer_name'] == selected_manufacturer]

# FAQ 표시
if not filtered_df.empty:
    for i, row in filtered_df.iterrows():
        with st.expander(f"Q. {row['question']} ({row['manufacturer_name']})"):
            st.write(row['answer'])
else:
    st.info("검색 조건에 맞는 FAQ가 없습니다.")