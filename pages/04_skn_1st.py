# app.py
import streamlit as st
import pandas as pd
import altair as alt
import re

# 0) 페이지 설정 - 반드시 첫 Streamlit 호출!
st.set_page_config(layout="wide", page_title="EV vs ICE 화재 현황 & EV FAQ")

# 🔹 화면 전환 (사이드바)
mode = st.sidebar.radio("화면 선택", ["대시보드", "EV FAQ"], index=0)

# 1) 데이터 로드 (예시 데이터 — CSV/DB로 교체 가능)
@st.cache_data
def load_sample_data():
    reg_raw = pd.DataFrame({
        "year": [2021,2021,2021, 2022,2022,2022, 2023,2023,2023, 2021,2022,2023],
        "fuel": ["Gasoline","Diesel","LPG", "Gasoline","Diesel","LPG",
                 "Gasoline","Diesel","LPG", "EV","EV","EV"],
        "count": [22000000, 2000000, 900000,
                  22400000, 2100000, 1100000,
                  22800000, 2100000, 1050000,
                  231443, 389855, 543900]
    })
    fire_raw = pd.DataFrame({
        "year": [2021,2021,2021, 2022,2022,2022, 2023,2023,2023, 2021,2022,2023],
        "fuel": ["Gasoline","Diesel","LPG", "Gasoline","Diesel","LPG",
                 "Gasoline","Diesel","LPG", "EV","EV","EV"],
        "fires": [3200, 230, 87,
                  3350, 240, 90,
                  3370, 260, 106,
                  24, 43, 72]
    })
    return reg_raw, fire_raw

reg_raw, fire_raw = load_sample_data()

# 공통 전처리 (ICE/EV 매핑)
EXCLUDE = {"hybrid", "phev", "hydrogen", "fuelcell"}
def to_group(f):
    f = f.strip().lower()
    if f in {"gasoline","diesel","lpg"}: return "ICE"
    if f in {"ev"}: return "EV"
    return None

reg_raw = reg_raw[~reg_raw["fuel"].str.lower().isin(EXCLUDE)].copy()
fire_raw = fire_raw[~fire_raw["fuel"].str.lower().isin(EXCLUDE)].copy()
reg_raw["group"]  = reg_raw["fuel"].apply(to_group)
fire_raw["group"] = fire_raw["fuel"].apply(to_group)
reg_raw.dropna(subset=["group"], inplace=True)
fire_raw.dropna(subset=["group"], inplace=True)

reg  = reg_raw.groupby(["year","group"], as_index=False)["count"].sum()
fire = fire_raw.groupby(["year","group"], as_index=False)["fires"].sum()
df = pd.merge(reg, fire, on=["year","group"], how="outer").fillna(0)
df["fire_rate_per_100k"] = (df["fires"] / df["count"]).replace([pd.NA, float("inf")], 0) * 100000

# ===========================
# A) 대시보드 화면
# ===========================
if mode == "대시보드":
    # 2) 스타일 & 배너
    BANNER_CSS = """
    <style>
    .hero { width:100%; height:340px;
      background-image:url('https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?q=80&w=1600');
      background-size:cover; background-position:center;
      border-radius:12px; position:relative; margin-bottom:16px; }
    .hero .overlay { position:absolute; inset:0;
      background:linear-gradient(180deg, rgba(0,0,0,0.25), rgba(0,0,0,0.55));
      border-radius:12px; }
    .hero .content { position:absolute; left:24px; bottom:22px; color:#fff; }
    .card-fixed { position:fixed; right:24px; bottom:24px; background:#fff;
      border-radius:16px; box-shadow:0 10px 30px rgba(0,0,0,0.18);
      padding:18px 20px; max-width:340px; z-index:9999;
      border:1px solid rgba(0,0,0,0.06); }
    .card-fixed h3{ margin:0 0 8px 0; }
    .metric{ display:flex; justify-content:space-between; gap:12px;
      padding:8px 0; border-top:1px dashed #eee; font-size:15px; }
    @media (max-width: 640px){ .card-fixed{ right:12px; left:12px; bottom:12px; } }
    </style>
    """
    st.markdown(BANNER_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="hero">
      <div class="overlay"></div>
      <div class="content">
        <h1>EV vs ICE 화재 현황</h1>
        <p>가솔린·디젤·LPG는 내연기관(ICE)으로 합산하여 EV와 비교합니다.</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 3) 컨트롤
    c1, c2, c3 = st.columns([1,1,1.2])
    with c1:
        years = sorted(df["year"].unique())
        year_sel = st.selectbox("연도 선택", options=["전체"] + years, index=0)
    with c2:
        metric_sel = st.radio("지표", ["등록대수", "화재건수", "화재율(건/10만대)"], horizontal=True)
    with c3:
        chart_type = st.radio("차트 유형", ["선 + 마커", "막대"], horizontal=True)
        st.caption("※ 하이브리드/수소차 제외")

    df_view = df if year_sel == "전체" else df[df["year"] == year_sel]
    value_col = {"등록대수":"count", "화재건수":"fires", "화재율(건/10만대)":"fire_rate_per_100k"}[metric_sel]

    plot_df = (
        df_view[["year","group",value_col]]
        .rename(columns={value_col: "value"})
        .sort_values(["year","group"])
    )

    COLOR_SCALE = alt.Scale(domain=["ICE","EV"], range=["#1f77b4", "#ff7f0e"])

    def make_chart(data: pd.DataFrame, chart_type: str, metric_label: str):
        base = alt.Chart(data).encode(
            x=alt.X("year:O", title="연도", axis=alt.Axis(labelAngle=0, grid=True)),
            y=alt.Y("value:Q", title=metric_label,
                    axis=alt.Axis(grid=True, tickCount=6, format="~s")),
            color=alt.Color("group:N", title="구분", scale=COLOR_SCALE),
            tooltip=[
                alt.Tooltip("year:O", title="연도"),
                alt.Tooltip("group:N", title="구분"),
                alt.Tooltip("value:Q", title=metric_label, format=",.3f" if "율" in metric_label else ",")
            ]
        ).properties(height=420)

        if chart_type == "막대":
            chart = base.mark_bar(size=28, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        else:
            line = base.mark_line(size=3)
            points = base.mark_point(size=70, filled=True)
            chart = line + points

        last_year = data["year"].max()
        labels = (
            alt.Chart(data[data["year"] == last_year])
            .mark_text(align="left", dx=6, dy=0, fontSize=12)
            .encode(
                x="year:O",
                y="value:Q",
                color=alt.Color("group:N", scale=COLOR_SCALE, legend=None),
                text=alt.Text("value:Q", format=",.2f" if "율" in metric_label else ",")
            )
        )
        return (chart + labels).configure_view(strokeOpacity=0)

    st.subheader(f"{metric_sel} (ICE vs EV)")
    y_label = "등록대수(대)" if metric_sel=="등록대수" else ("화재건수(건)" if metric_sel=="화재건수" else "화재율(건/10만대)")
    chart = make_chart(plot_df, chart_type, y_label)
    st.altair_chart(chart, use_container_width=True)

    # 4) 오른쪽 하단 카드(핵심 요약) — 대시보드에서만 렌더
    def latest_val(group, col):
        d = df_view[df_view["group"] == group]
        if d.empty: return 0.0
        if year_sel == "전체":
            y = d["year"].max()
            d = d[d["year"] == y]
        return float(d[col].sum())

    ice_cnt  = latest_val("ICE", "count")
    ev_cnt   = latest_val("EV",  "count")
    ice_fire = latest_val("ICE", "fires")
    ev_fire  = latest_val("EV",  "fires")
    ice_rate = (ice_fire / ice_cnt * 100000) if ice_cnt else 0.0
    ev_rate  = (ev_fire  / ev_cnt  * 100000) if ev_cnt  else 0.0

    card_html = f"""
    <div class="card-fixed">
      <h3>요약 • {'전체' if year_sel=='전체' else year_sel}</h3>
      <div class="metric"><b>ICE 등록</b><span>{ice_cnt:,.0f} 대</span></div>
      <div class="metric"><b>EV 등록</b><span>{ev_cnt:,.0f} 대</span></div>
      <div class="metric"><b>ICE 화재</b><span>{ice_fire:,.0f} 건</span></div>
      <div class="metric"><b>EV 화재</b><span>{ev_fire:,.0f} 건</span></div>
      <div class="metric"><b>ICE 화재율</b><span>{ice_rate:,.3f} 건/10만대</span></div>
      <div class="metric"><b>EV 화재율</b><span>{ev_rate:,.3f} 건/10만대</span></div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

# ===========================
# B) EV FAQ 화면
# ===========================
else:
    # 1) FAQ 스타일
    FAQ_CSS = """
    <style>
    .faq-title { text-align:center; margin:24px 0 8px 0; }
    .faq-title h1 { font-size:56px; font-weight:800; letter-spacing:-0.5px; margin:0; }
    .faq-sub { text-align:center; margin:4px 0 24px 0; color:#23303A; }
    .faq-list { max-width:1200px; margin:0 auto; }
    details { border-top:1px solid #E5E7EB; margin:0; }
    details:last-of-type { border-bottom:1px solid #E5E7EB; }
    summary {
      list-style:none; cursor:pointer; padding:18px 8px;
      font-size:20px; display:flex; justify-content:space-between; align-items:center;
    }
    summary::-webkit-details-marker { display:none; }
    summary .qtext { flex:1; color:#0F1E25; }
    summary .plus { width:24px; height:24px; position:relative; }
    summary .plus:before, summary .plus:after {
      content:""; position:absolute; background:#0F1E25;
      left:50%; top:50%; transform:translate(-50%, -50%);
    }
    summary .plus:before { width:2px; height:18px; }  /* 세로 */
    summary .plus:after  { width:18px; height:2px; }  /* 가로 */
    details[open] summary .plus:before { height:0; }  /* + -> - */
    .answer { padding:0 8px 20px 8px; color:#334155; line-height:1.6; font-size:16px; }
    .badge { display:inline-block; padding:4px 10px; border-radius:9999px; background:#EFF6FF; color:#1D4ED8; font-size:12px; font-weight:600; margin-right:8px; }
    .search-row { max-width:1200px; margin:10px auto 18px auto; }
    </style>
    """
    st.markdown(FAQ_CSS, unsafe_allow_html=True)

    # 2) 제조사별 FAQ 데이터
    BRANDS = {
        "기아": [
            {"cat":"충전", "q":"EV6의 충전 도어 안쪽 번개 버튼 기능은 무엇인가요?",
             "a":"충전 포트 잠금/해제 및 수동 해제용으로 사용됩니다. 경고등 신호와 함께 동작하며, 사용자 설명서를 참고하세요."},
            {"cat":"안전/화재", "q":"전기차 충전기 연결 후 고전압 배터리가 충전 안되면?",
             "a":"커넥터 재결합, 다른 충전기 시도, 12V 보조배터리 전압 확인 후 계속되면 서비스센터 점검을 권장합니다."},
            {"cat":"혜택/카드", "q":"친환경 전기차 충전카드는 어떻게 발급받나요?",
             "a":"제휴 카드사/모빌리티 앱에서 신청 가능하며, 멤버십 연동으로 할인과 실적 적립이 제공됩니다."},
        ],
        "현대": [
            {"cat":"안전/화재", "q":"고전압 배터리는 화재 및 폭발에 안전한가요?",
             "a":"다중 안전장치(BMS, 절연, 냉각)와 충돌 시험 기준을 충족합니다. 과열·침수 등 특수 상황은 즉시 점검받으세요."},
            {"cat":"전자파", "q":"전기차의 전자파가 인체에 유해하지 않나요?",
             "a":"실내 전자기장 노출은 국제 권고 기준(IEC/ICNIRP) 이내로 측정되며, 일반 가전 수준입니다."},
            {"cat":"겨울/효율", "q":"겨울에 주행거리가 줄어드는 이유와 대책은?",
             "a":"저온에서 화학 반응성 저하로 효율이 감소합니다. 예열, 히트펌프/스티어링 휠열선, 에코모드 활용이 도움이 됩니다."},
        ],
        "테슬라": [
            {"cat":"충전", "q":"슈퍼차저 이용 시 배터리 예열이 필요한가요?",
             "a":"내비에서 슈퍼차저 목적지 설정 시 자동으로 배터리 컨디셔닝이 수행되어 충전 속도를 최적화합니다."},
            {"cat":"소프트웨어", "q":"OTA 업데이트가 주행거리에 영향을 주나요?",
             "a":"일부 업데이트는 효율·열관리 로직을 개선할 수 있으나, 실제 영향은 모델/버전에 따라 상이합니다."},
            {"cat":"정비", "q":"서비스 예약은 어떻게 하나요?",
             "a":"모바일 앱에서 증상 입력 후 모바일 서비스 또는 서비스센터 방문을 선택할 수 있습니다."},
        ],
    }

    # 3) 상단 타이틀 + 제조사 탭 + 검색
    st.markdown('<div class="faq-title"><h1>전기차 FAQ</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="faq-sub">제조사를 선택해 자주 묻는 질문을 확인하세요.</div>', unsafe_allow_html=True)

    tabs = st.tabs(list(BRANDS.keys()))  # ["기아","현대","테슬라"]

    with st.container():
        st.markdown('<div class="search-row"></div>', unsafe_allow_html=True)
        col_s1, col_s2 = st.columns([2,1])
        with col_s1:
            query = st.text_input("🔎 키워드 검색 (예: 충전, 겨울, 전자파)", "")
        with col_s2:
            st.write("")
            st.caption("※ 키워드가 질문/답변에 포함된 항목만 표시됩니다.")

    def render_brand_tab(tab, brand_name, items, query):
        with tab:
            filtered = items
            if query:
                pat = re.compile(re.escape(query), re.IGNORECASE)
                filtered = [it for it in items if pat.search(it["q"]) or pat.search(it["a"])]
            st.markdown('<div class="faq-list">', unsafe_allow_html=True)
            if not filtered:
                st.info("검색 결과가 없습니다. 키워드를 바꾸어보세요.")
            else:
                for i, it in enumerate(filtered, start=1):
                    q_html = f"""
                    <details>
                      <summary>
                        <span class="qtext">{it['q']}</span>
                        <span class="plus"></span>
                      </summary>
                      <div class="answer">
                        <span class="badge">{it['cat']}</span>
                        {it['a']}
                      </div>
                    </details>
                    """
                    st.markdown(q_html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    for tab, brand in zip(tabs, BRANDS.keys()):
        render_brand_tab(tab, brand, BRANDS[brand], query)
