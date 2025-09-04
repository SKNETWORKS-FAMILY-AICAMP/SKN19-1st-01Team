import streamlit as st
from matplotlib import rc
import pandas as pd
from bokeh.plotting import figure
import sys # Add sys import
import os # Add os import
import altair as alt # Add altair import for advanced charting

# Add the parent directory to the Python path to enable importing connection.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db')))

from connection import get_connection # DB 연결
import mysql.connector # 에러 핸들링용

# --- DB에서 데이터 로드 함수 ---
def load_registration_data():
    conn = None
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            # vehicle_registrations 테이블에서 데이터 가져오기
            cursor.execute("SELECT year, fuel_type, count FROM vehicle_registrations")
            df = pd.DataFrame(cursor.fetchall())
            
            # ICE와 EV로 분류
            
            # ICE 등록대수
            ice_reg = df[df['fuel_type'] == 'ICE'].copy()
            ice_reg.rename(columns={'year': '연도', 'count': '등록대수'}, inplace=True)
            ice_reg['연료'] = 'ICE'
            
            # EV 등록대수
            ev_reg = df[df['fuel_type'] == 'EV'].copy()
            ev_reg.rename(columns={'year': '연도', 'count': '등록대수'}, inplace=True)
            ev_reg['연료'] = 'EV'
            
            # 두 데이터프레임 합치기
            reg_df = pd.concat([ice_reg, ev_reg], ignore_index=True)
            return reg_df
    except mysql.connector.Error as err:
        st.error(f"등록 데이터 로드 중 오류 발생: {err}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def load_fire_incident_data():
    conn = None
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # total_fire_incidents (ICE 포함 전체)
            cursor.execute("SELECT year, total_fires FROM total_fire_incidents")
            total_fire_df = pd.DataFrame(cursor.fetchall())
            total_fire_df.rename(columns={'year': '연도', 'total_fires': '화재 발생 수'}, inplace=True) # Rename 'year' to '연도'
            total_fire_df['연료'] = 'ICE' # 임시로 ICE로 간주 (전체 차량 화재)

            # ev_fire_cases (EV 화재)
            cursor.execute("SELECT year, total_fires FROM ev_fire_cases")
            ev_fire_df = pd.DataFrame(cursor.fetchall())
            ev_fire_df.rename(columns={'year': '연도', 'total_fires': '화재 발생 수'}, inplace=True) # Rename 'year' to '연도'
            ev_fire_df['연료'] = 'EV'
            
            # 두 데이터프레임 합치기
            fire_df = pd.concat([total_fire_df, ev_fire_df], ignore_index=True)
            return fire_df
    except mysql.connector.Error as err:
        st.error(f"화재 발생 데이터 로드 중 오류 발생: {err}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def calculate_fire_rates_per_registration(reg_df, fire_df):
    if reg_df.empty or fire_df.empty:
        return pd.DataFrame()
    
    # 등록대수와 화재 발생 수를 병합
    merged_df = pd.merge(reg_df, fire_df, on=['연도', '연료'], how='inner')
    
    # 화재율 계산 (비율)
    merged_df['화재율'] = (merged_df['화재 발생 수'] / merged_df['등록대수']) * 100000 # Calculate per 100,000 registrations
    
    return merged_df[['연도', '연료', '화재율']]

def load_faq_data_from_db():
    conn = None
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            # EV_Manufacturer_FAQ 테이블에서 FAQ 데이터 가져오기
            # 제조사 이름도 함께 가져오기 위해 JOIN
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

# --- Streamlit 앱 시작 ---
st.set_page_config(
    page_title="EV vs ICE 화재 현황",
    page_icon="🔥",
    layout="wide"
)

st.title("⚡ EV vs 🚗 ICE 화재 현황")

# 1. 등록대수 데이터
st.subheader("차량 등록 현황")
reg = load_registration_data()
if not reg.empty:
    col_reg1, col_reg2 = st.columns(2)
    with col_reg1:
        st.subheader("🚗 ICE 차량 등록 현황")
        ice_reg_df = reg[reg['연료'] == 'ICE'].pivot_table(index="연도", values="등록대수")
        st.line_chart(ice_reg_df)
    with col_reg2:
        st.subheader("⚡ EV 차량 등록 현황")
        ev_reg_df = reg[reg['연료'] == 'EV'].pivot_table(index="연도", values="등록대수")
        st.line_chart(ev_reg_df)
else:
    st.warning("등록 데이터를 불러오지 못했습니다. DB 연결 및 테이블을 확인해주세요.")

# 2. 화재 발생 현황
st.subheader("차량 화재 현황")
reg_data = load_fire_incident_data()
reg = load_registration_data() # 등록대수 데이터도 필요

if not reg_data.empty and not reg.empty:
    col1, col2 = st.columns(2) # 2개의 컬럼 생성

    with col1:
        st.subheader("📈 ICE 연도별 화재 건수")
        ice_fire_df = reg_data[reg_data['연료'] == 'ICE'].pivot_table(index="연도", values="화재 발생 수")
        st.line_chart(ice_fire_df)
    with col2:
        st.subheader("📈 EV 연도별 화재 건수")
        ev_fire_df = reg_data[reg_data['연료'] == 'EV'].pivot_table(index="연도", values="화재 발생 수")
        st.line_chart(ev_fire_df)

    with col1:
        st.subheader("📊 등록대수 10만 건당 화재 발생 횟수")
    fire_rates_df = calculate_fire_rates_per_registration(reg, reg_data)
    if not fire_rates_df.empty:
        chart = alt.Chart(fire_rates_df).mark_bar().encode(
            x=alt.X('연도:O', axis=alt.Axis(title='연도')),
            y=alt.Y('화재율:Q', axis=alt.Axis(title='10만 건당 화재 발생 횟수')),
            color='연료:N',
            xOffset='연료:N', # This creates grouped bars
            tooltip=['연도', '연료', '화재율']
        ).properties(
            title='등록대수 10만 건당 화재 발생 횟수'
        ).configure_axis(
            labelAngle=0
        ).interactive()
        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("화재율 데이터를 계산할 수 없습니다.")
else:
    st.warning("화재 현황 데이터를 불러오지 못했습니다. DB 연결 및 테이블을 확인해주세요.")