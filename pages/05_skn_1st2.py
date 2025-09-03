#PS C:\skn_19\python_b> cd 10_Streamlit   
#PS C:\skn_19\python_b\10_Streamlit> streamlit run 01_main.py

import streamlit as st
import pandas as pd
from bokeh.plotting import figure

st.title("EV vs ICE 화재 현황 & EV FAQ")


reg = pd.DataFrame([
        {"연료": "ICE", "연도": 2021, "등록대수": 24911101},  # 가솔린+디젤+LPG 합산
        {"연료": "ICE", "연도": 2022, "등록대수": 25503078},
        {"연료": "ICE", "연도": 2023, "등록대수": 25949201},
        {"연료": "EV",  "연도": 2021, "등록대수": 231443},
        {"연료": "EV",  "연도": 2022, "등록대수": 389855},
        {"연료": "EV",  "연도": 2023, "등록대수": 543900},
    ]
)
st.dataframe(reg)


reg_data = pd.DataFrame([
    {"연료": "ICE", "연도": 2021, "화재 발생 수": 3517},  # 가솔린+디젤+LPG 합산
    {"연료": "ICE", "연도": 2022, "화재 발생 수": 3680},
    {"연료": "ICE", "연도": 2023, "화재 발생 수": 3736},
    {"연료": "EV",  "연도": 2021, "화재 발생 수": 24},
    {"연료": "EV",  "연도": 2022, "화재 발생 수": 43},
    {"연료": "EV",  "연도": 2023, "화재 발생 수": 72},
])

st.dataframe(reg_data)

# 연도별 ICE vs EV 비교용 피벗 테이블
chart_df = reg_data.pivot_table(index="연도", columns="연료", values="화재 발생 수")

st.subheader("📈 ICE vs EV 연도별 화재 건수 - 선그래프")
st.line_chart(chart_df)

reg_list = pd.DataFrame([
    {"연료": "ICE", "연도": 2021, "화재율": 14.124},  # 가솔린+디젤+LPG 합산
    {"연료": "ICE", "연도": 2022, "화재율": 14.375},
    {"연료": "ICE", "연도": 2023, "화재율": 14.397},
    {"연료": "EV",  "연도": 2021, "화재율":10.373},
    {"연료": "EV",  "연도": 2022, "화재율": 11.030},
    {"연료": "EV",  "연도": 2023, "화재율": 13.24},
])
st.dataframe(reg_list)

chart_df = reg_list.pivot_table(index="연도", columns="연료", values="화재율")

st.subheader("📈 화재율(건/10만대) (ICE vs EV)")
st.line_chart(chart_df)


st.header("❓ EV FAQ — 브랜드별")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("현대")
    with st.expander("Q1. 현대 전기차 화재율은?"):
        st.write("내연기관 대비 낮은 편입니다.")
    with st.expander("Q2. 배터리 안전 기술은?"):
        st.write("배터리 팩 차단 장치, 냉각 시스템 등을 적용합니다.")

with col2:
    st.subheader("기아")
    with st.expander("Q1. 기아 EV 화재 사례는?"):
        st.write("국내외에서 일부 사례가 있으나 빈도는 낮습니다.")
    with st.expander("Q2. 예방책은?"):
        st.write("정기 점검 및 충전 습관 관리가 중요합니다.")

with col3:
    st.subheader("테슬라")
    with st.expander("Q1. 테슬라 화재는 왜 주목받나요?"):
        st.write("미디어 노출이 많아 실제 빈도보다 위험성이 크게 인식됩니다.")
    with st.expander("Q2. 안전 장치는?"):
        st.write("소프트웨어 업데이트, 배터리 관리 시스템이 있습니다.")




