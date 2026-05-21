import streamlit as st
import pandas as pd
import os
import re

# --- [UI/UX] 요즘 대학생들이 좋아하는 미니멀 파스텔 & 프리텐다드 폰트 스타일링 ---
st.set_page_config(page_title="YONSEI GS-ED Timetable", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;800&display=swap');
        * { font-family: 'Pretendard', sans-serif !important; }
        
        .main-title { font-size: 2rem; font-weight: 800; color: #112F6F; margin-bottom: 5px; }
        .sub-title { font-size: 0.95rem; color: #64748B; margin-bottom: 25px; }
        
        /* 테이블 및 디자인 카드 컴포넌트 */
        .card { background-color: #F8FAFC; padding: 18px; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 12px; }
        .course-list-item { padding: 12px; background-color: #F1F5F9; border-radius: 10px; margin-bottom: 8px; border-left: 5px solid #112F6F; }
        
        .stTabs [data-baseweb="tab"] { font-weight: 600; color: #64748B; font-size: 16px; padding: 10px 20px; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #112F6F !important; border-bottom-color: #112F6F !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🦅 연세대학교 교육대학원 시간표 도우미</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">2025학년도 2학기 수강신청 시뮬레이터 시스템</div>', unsafe_allow_html=True)

PREDEFINED_COLORS = ["#E2EFFE", "#FEE2E2", "#FEF3C7", "#E0F2FE", "#ECEFEE", "#F3E8FF", "#ECFDF5", "#FFF1F2", "#F0FDFA", "#EFF6FF"]

# ==========================================
#  🔥 CORE: 연세교대원 특유의 CSV 구조 완벽 파싱 엔진
# ==========================================
@st.cache_data
def load_and_parse_yonsei_csv():
    file_path = "time_table1(2025-2).xls - 2025-2.csv"
    if not os.path.exists(file_path):
        return pd.DataFrame()
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    parsed_courses = []
    current_major = "공통/교직"
    
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        if line and not line.startswith(",") and ",,,," in line:
            current_major = line.split(",")[0].strip()
            idx += 1
            continue
            
        if "구      분" in line:
            header_parts = [p.strip() for p in line.split(",")]
            days_in_block = [p for p in header_parts if p in ["월", "화", "수", "목", "금"]]
            idx += 1
            while idx < len(lines) and "구      분" not in lines[idx] and ",,,," not in lines[idx]:
                block_line = lines[idx].strip()
                if "1,2교시" in block_line: current_period = "1,2"
                elif "3,4교시" in block_line: current_period = "3,4"
                    
                if "과 목 종 별" in block_line:
                    try:
                        types = lines[idx].strip().split(",")[2:]
                        codes = lines[idx+1].strip().split(",")[2:]
                        names = lines[idx+2].strip().split(",")[2:]
                        profs = lines[idx+3].strip().split(",")[2:]
                        rooms = lines[idx+4].strip().split(",")[2:]
                        
                        for col_idx, day in enumerate(days_in_block):
                            if col_idx < len(names) and names[col_idx].strip():
                                c_name = names[col_idx].strip()
                                if "(영어)" in codes[col_idx]: c_name += " (영어)"
                                h_code = codes[col_idx].split("(")[0].strip()
                                credit = 2 if "SPT" in h_code else 3
                                
                                final_major = current_major
                                if "교직" in current_major:
                                    if "SPT" in h_code: final_major = "교직(자격증)"
                                    elif "SPL" in h_code: final_major = "평생교육사"
                                    else: final_major = "교직(공통)"
                                
                                parsed_courses.append({
                                    "전공": final_major, "요일": day, "교시": current_period,
                                    "과목종별": types[col_idx].strip() if col_idx < len(types) else "전공",
                                    "학정번호": h_code, "과목명": c_name,
                                    "교수명": profs[col_idx].strip() if col_idx < len(profs) else "미지정",
                                    "강의실": rooms[col_idx].strip() if col_idx < len(rooms) else "미지정",
                                    "학점": credit, "type": "교직" if "교직" in final_major or "평생" in final_major else "전공"
                                })
                    except Exception: pass
                    idx += 5
                    continue
                idx += 1
            continue
        idx += 1

    df = pd.DataFrame(parsed_courses).drop_duplicates(subset=['학정번호', '요일', '교시'])
    df['time_slots_set'] = df.apply(lambda r: set((r['요일'], int(p)) for p in r['교시'].split(',')), axis=1)
    return df

master_df = load_and_parse_yonsei_csv()

if 'my_courses' not in st.session_state: st.session_state.my_courses = []
if 'color_map' not in st.session_state: st.session_state.color_map = {}

# --- [경고 해결] st.query_params 최신 버전 교체 ---
query_dict = st.query_params.to_dict()
if "courses" in query_dict and not st.session_state.my_courses:
    try:
        courses_str = query_dict["courses"]
        if courses_str:
            shared_courses = [c for c in courses_str.split(',') if not master_df[master_df['학정번호'] == c].empty]
            if shared_courses:
                st.session_state.my_courses = shared_courses
                for h_no in shared_courses:
                    name = master_df[master_df['학정번호'] == h_no].iloc[0]['과목명']
                    if name not in st.session_state.color_map:
                        st.session_state.color_map[name] = PREDEFINED_COLORS[len(st.session_state.color_map) % len(PREDEFINED_COLORS)]
                st.rerun()
    except Exception:
        for key in list(st.query_params.keys()): del st.query_params[key]

# 중복 시간 자동 필터링 기능
def get_available_courses(df, selected_ids):
    if not selected_ids: return df
    available_df = df[~df['학정번호'].isin(selected_ids)]
    my_busy_slots = set().union(*df[df['학정번호'].isin(selected_ids)]['time_slots_set'])
    return available_df[available_df['time_slots_set'].apply(lambda s: s.isdisjoint(my_busy_slots))]

available_df = get_available_courses(master_df, st.session_state.my_courses)

# ==========================================
#  📍 원래 디자인 복구: 상단 1. 과목 선택 영역
# ==========================================
st.subheader("1. 과목 선택")
tab_major, tab_general = st.tabs(["🎓 전공 과목 선택", "🍎 교직 및 공통 과목 선택"])

# 공통 포맷팅 헬퍼
def format_selectbox_str(row):
    return f"[{row['과목종별']}] {row['과목명']} ({row['교수명']} / {row['요일']}요일 {row['교시']}교시 / {row['강의실']}) - {row['학점']}학점 [{row['학정번호']}]"

# --- 1) 전공 과목 탭 ---
with tab_major:
    col1, col2 = st.columns(2)
    with col1:
        major_list = sorted([m for m in master_df['전공'].unique() if "교직" not in m and "평생" not in m])
        selected_major = st.selectbox("전공 학부(과)", major_list, key="major_select_box")
    with col2:
        search_major = st.text_input("🔎 전공 과목명 또는 교수명 검색", placeholder="검색어 입력...", key="search_major_box")
        
    final_filtered_major = available_df[available_df['전공'] == selected_major]
    if search_major:
        final_filtered_major = final_filtered_major[final_filtered_major['과목명'].str.lower().str.contains(search_major.lower()) | final_filtered_major['교수명'].str.lower().str.contains(search_major.lower())]
        
    if not final_filtered_major.empty:
        selected_idx = st.selectbox("추가할 전공 과목 선택", options=final_filtered_major.index, format_func=lambda idx: format_selectbox_str(final_filtered_major.loc[idx]), label_visibility="collapsed")
        if st.button("전공 추가", use_container_width=True, type="primary"):
            row = final_filtered_major.loc[selected_idx]
            st.session_state.my_courses.append(row['학정번호'])
            st.session_state.color_map[row['과목명']] = PREDEFINED_COLORS[len(st.session_state.color_map) % len(PREDEFINED_COLORS)]
            st.query_params["courses"] = ",".join(st.session_state.my_courses)
            st.success(f"✅ '{row['과목명']}' 과목을 추가했습니다.")
            st.rerun()
    else:
        st.warning("선택한 조건에 현재 추가 가능한 전공 과목이 없습니다.")

# --- 2) 교직 과목 탭 ---
with tab_general:
    col1, col2 = st.columns(2)
    with col1:
        kyojik_list = ["전체", "교직(공통)", "교직(자격증)", "평생교육사"]
        selected_kyojik = st.selectbox("교직/공통 구분", kyojik_list, key="kyojik_select_box")
    with col2:
        search_kyojik = st.text_input("🔎 교직 과목명 또는 교수명 검색", placeholder="검색어 입력...", key="search_kyojik_box")
        
    final_filtered_k = available_df[available_df['전공'].str.contains("교직|평생")]
    if selected_kyojik != "전체":
        final_filtered_k = final_filtered_k[final_filtered_k['전공'] == selected_kyojik]
    if search_kyojik:
        final_filtered_k = final_filtered_k[final_filtered_k['과목명'].str.lower().str.contains(search_kyojik.lower()) | final_filtered_k['교수명'].str.lower().str.contains(search_kyojik.lower())]
        
    if not final_filtered_k.empty:
        selected_idx_k = st.selectbox("추가할 교직 과목 선택", options=final_filtered_k.index, format_func=lambda idx: format_selectbox_str(final_filtered_k.loc[idx]), label_visibility="collapsed")
        if st.button("교직 추가", use_container_width=True, type="primary"):
            row = final_filtered_k.loc[selected_idx_k]
            st.session_state.my_courses.append(row['학정번호'])
            st.session_state.color_map[row['과목명']] = PREDEFINED_COLORS[len(st.session_state.color_map) % len(PREDEFINED_COLORS)]
            st.query_params["courses"] = ",".join(st.session_state.my_courses)
            st.success(f"✅ '{row['과목명']}' 과목을 추가했습니다.")
            st.rerun()
    else:
        st.warning("선택한 조건에 현재 추가 가능한 교직 과목이 없습니다.")

st.divider()

# ==========================================
#  📍 원래 디자인 복구: 하단 2. 나의 시간표 영역
# ==========================================
st.subheader("2. 나의 시간표")

if not st.session_state.my_courses:
    st.info("과목을 추가하면 시간표가 여기에 표시됩니다.")
else:
    my_df = master_df[master_df['학정번호'].isin(st.session_state.my_courses)].drop_duplicates(subset=['학정번호'])
    total_credits = my_df['학점'].sum()
    
    # 상단 요약 헤더 바 및 초기화 레이아웃 복구
    list_col, action_col = st.columns([0.85, 0.15])
    with list_col:
        st.markdown(f"#### 📝 선택한 과목 내역 [총 {len(my_df)}과목, {total_credits}학점]")
    with action_col:
        if st.button("전체 초기화", type="primary", use_container_width=True):
            st.session_state.my_courses, st.session_state.color_map = [], {}
            for key in list(st.query_params.keys()): del st.query_params[key]
            st.rerun()
            
    # --- HTML / CSS 인스타 감성 한 스푼 섞인 대학원 그리드 뷰포트 생성 ---
    days = ['월', '화', '수', '목', '금']
    periods = [1, 2, 3, 4]
    time_labels = {1: "1교시<br><small>18:20-19:10</small>", 2: "2교시<br><small>19:15-20:05</small>", 3: "3교시<br><small>20:10-21:00</small>", 4: "4교시<br><small>21:05-21:55</small>"}
    grid = {(p, d): {"text": "", "color": "#FFFFFF", "span": 1, "visible": True} for p in periods for d in days}
    
    for _, row in master_df[master_df['학정번호'].isin(st.session_state.my_courses)].iterrows():
        color = st.session_state.color_map.get(row['과목명'], "#FFFFFF")
        p_list = sorted([int(p) for p in row['교시'].split(',')])
        if len(p_list) == 2 and p_list[1] == p_list[0] + 1:
            grid[(p_list[0], row['요일'])] = {
                "text": f"<div style='font-weight:700; color:#1E293B;'>{row['과목명']}</div><div style='font-size:11px; margin-top:3px; color:#64748B;'>{row['교수명']}<br>{row['강의실']}</div>",
                "color": color, "span": 2, "visible": True
            }
            grid[(p_list[1], row['요일'])]["visible"] = False
        else:
            for p in p_list:
                grid[(p, row['요일'])] = {
                    "text": f"<div style='font-weight:700; color:#1E293B;'>{row['과목명']}</div><div style='font-size:11px; margin-top:3px; color:#64748B;'>{row['교수명']}<br>{row['강의실']}</div>",
                    "color": color, "span": 1, "visible": True
                }

    table_html = """
    <div id="capture-area" style="padding: 5px; background: #ffffff; border-radius: 12px;">
    <table style="width:100%; border-collapse:separate; border-spacing: 5px; text-align:center; table-layout:fixed;">
        <thead>
            <tr style="height:40px; background-color:#F1F5F9;">
                <th style="border-radius:6px; color:#475569; font-size:13px; font-weight:600; width:12%;">교시</th>
    """
    for d in days:
        table_html += f'<th style="border-radius:6px; color:#475569; font-size:13px; font-weight:600;">{d}</th>'
    table_html += '</tr></thead><tbody>'
    
    for p in periods:
        table_html += f'<tr style="height:80px;"><td style="background-color:#F8FAFC; border-radius:6px; color:#64748B; font-size:12px; font-weight:600; padding:4px; line-height:1.3;">{time_labels[p]}</td>'
        for d in days:
            cell = grid[(p, d)]
            if cell["visible"]:
                bg = cell["color"]
                border_style = "border-radius: 8px;" if cell["text"] else "border-radius: 8px; background-color:#F8FAFC; border: 1px dashed #E2E8F0;"
                table_html += f'<td rowspan="{cell["span"]}" style="{border_style} background-color:{bg}; padding:8px; font-size:12px;">{cell["text"]}</td>'
        table_html += '</tr>'
    table_html += '</tbody></table></div>'

    js_downloader = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <button id="download-btn" style="margin-top:12px; padding:10px 20px; background-color:#112F6F; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:600; font-size:14px;">시간표 이미지로 저장</button>
    <div id="status-log" style="margin-top:5px; font-size:12px;"></div>
    <script>
        document.getElementById('download-btn').onclick = function() {
            const area = document.getElementById("capture-area");
            const log = document.getElementById('status-log');
            log.innerText = '이미지 생성 중...'; log.style.color = '#112F6F';
            html2canvas(area, {scale: 3, backgroundColor: '#ffffff'}).then(canvas => {
                const a = document.createElement("a");
                a.href = canvas.toDataURL("image/png");
                a.download = "2026-1학기_시간표.png";
                document.body.appendChild(a); a.click(); document.body.removeChild(a);
                log.innerText = '✅ 이미지 다운로드가 시작되었습니다.'; log.style.color = '#059669';
            }).catch(e => { log.innerText = '❌ 에러: ' + e; log.style.color = '#DC2626'; });
        };
    </script>
    """
    st.components.v1.html(table_html + js_downloader, height=450)
    
    st.info("💡 시간표를 공유하려면 현재 브라우저의 주소창에 있는 전체 URL을 복사하여 전달하세요.")
    st.write("---")
    
    # --- 장바구니 리스트 및 개별 제거 버튼 인터페이스 구현 ---
    for index, (code, no) in enumerate(st.session_state.my_courses):
        course_rows = master_df[master_df['학정번호'] == code]
        if course_rows.empty: continue
        course = course_rows.iloc[0]
        
        col_list_item, col_del_btn = st.columns([0.88, 0.12])
        with col_col_list_item if 'col_col_list_item' in locals() else col_list_item:
            st.markdown(f"""
            <div class="card" style="padding: 12px; margin-bottom: 0px;">
                <span style="background-color:#E0F2FE; color:#0369A1; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600; margin-right:6px;">{course['과목종별']}</span>
                <strong style="font-size:14px; color:#1E293B;">{course['과목명']}</strong>
                <span style="font-size:13px; color:#64748B;"> ({course['교수명']} 교수님 / {course['요일']}요일 {course['교시']}교시)</span>
                <div style="font-size:11px; color:#94A3B8; margin-top:2px;">학정번호: {course['학정번호']} | 강의실: {course['강의실']} | {course['학점']}학점</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_del_btn:
            # 기존 제거 작동 로직 100% 매핑 고정
            if st.button("제거", key=f"del-{code}-{index}", use_container_width=True, type="secondary"):
                st.session_state.my_courses.pop(index)
                updated_courses_param = ",".join([f"{c}" for c in st.session_state.my_courses])
                if updated_courses_param:
                    st.query_params["courses"] = updated_courses_param
                else:
                    for key in list(st.query_params.keys()): del st.query_params[key]
                st.rerun()
