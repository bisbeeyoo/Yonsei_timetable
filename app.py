import streamlit as st
import pandas as pd
import os
import re

# ==========================================
#  🔥 CORE: 업로드된 엑셀 파일을 파싱하는 엔진으로 개조
# ==========================================
@st.cache_data
def load_and_parse_yonsei_excel(uploaded_file):
    """
    고정된 경로 대신, 사용자가 업로드한 파일 객체(uploaded_file)를 받아
    엑셀 데이터를 기존 파싱 엔진용 텍스트 라인 형태로 변환 후 파싱합니다.
    """
    if uploaded_file is None:
        return pd.DataFrame()
    
    try:
        # 업로드된 파일 객체를 pandas가 바로 읽도록 수정 (xls, xlsx 모두 지원)
        excel_df = pd.read_excel(uploaded_file, header=None)
        
        # 각 행을 쉼표(,)로 연결된 문자열 리스트로 변환
        lines = []
        for idx, row in excel_df.iterrows():
            line_str = ",".join([str(val).strip() if pd.notna(val) else "" for val in row])
            lines.append(line_str + "\n")
    except Exception as e:
        st.error(f"❌ 엑셀 파일을 읽는 중 오류가 발생했습니다. 올바른 시간표 파일인지 확인해 주세요: {e}")
        return pd.DataFrame()
        
    parsed_courses = []
    current_major = "공통/교직"
    
    # 텍스트 라인을 순회하며 블록 구조 해석
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        
        # 1. 전공 헤더 트래킹 (예: 교육공학,,,,주임교수...)
        if line and not line.startswith(",") and ",,,," in line:
            current_major = line.split(",")[0].strip()
            idx += 1
            continue
            
        # 2. 시간표 데이터 행 수집 (구분,,월,화,목 형태로 시작하는 블록 찾기)
        if "구      분" in line:
            header_parts = [p.strip() for p in line.split(",")]
            days_in_block = [p for p in header_parts if p in ["월", "화", "수", "목", "금"]]
            
            # 다음 행들에서 1,2교시 또는 3,4교시 블록 데이터 파싱
            idx += 1
            while idx < len(lines) and "구      분" not in lines[idx] and ",,,," not in lines[idx]:
                block_line = lines[idx].strip()
                
                # 교시 정보 포착 (1,2교시 또는 3,4교시)
                if "1,2교시" in block_line:
                    current_period = "1,2"
                elif "3,4교시" in block_line:
                    current_period = "3,4"
                    
                if "과 목 종 별" in block_line:
                    # 과목들의 묶음 시작점 포착 (종별, 학정번호, 과목명, 교수명, 강의실 세트 추출)
                    try:
                        types = lines[idx].strip().split(",")[2:]
                        codes = lines[idx+1].strip().split(",")[2:]
                        names = lines[idx+2].strip().split(",")[2:]
                        profs = lines[idx+3].strip().split(",")[2:]
                        rooms = lines[idx+4].strip().split(",")[2:]
                        
                        # 각 요일 열에 매핑된 데이터 파싱
                        for col_idx, day in enumerate(days_in_block):
                            if col_idx < len(names) and names[col_idx].strip():
                                c_name = names[col_idx].strip()
                                # 영어 분반 명칭 예쁘게 다듬기
                                if "(영어)" in codes[col_idx]:
                                    c_name += " (영어)"
                                    
                                h_code = codes[col_idx].split("(")[0].strip()
                                
                                # 데이터셋 보정 및 학점 부여 (자격증 교직은 2학점, 나머지는 대개 3학점)
                                credit = 2 if "SPT" in h_code else 3
                                
                                # 전공 분류 태깅 세분화
                                final_major = current_major
                                if "교직" in current_major:
                                    if "SPT" in h_code: final_major = "교직(자격증)"
                                    elif "SPL" in h_code: final_major = "평생교육사"
                                    else: final_major = "교직(공통)"
                                
                                parsed_courses.append({
                                    "전공": final_major,
                                    "요일": day,
                                    "교시": current_period,
                                    "과목종별": types[col_idx].strip() if col_idx < len(types) else "전공",
                                    "학정번호": h_code,
                                    "과목명": c_name,
                                    "교수명": profs[col_idx].strip() if col_idx < len(profs) else "미지정",
                                    "강의실": rooms[col_idx].strip() if col_idx < len(rooms) else "미지정",
                                    "학점": credit
                                })
                    except Exception:
                        pass
                    idx += 5
                    continue
                idx += 1
            continue
        idx += 1

    df = pd.DataFrame(parsed_courses).drop_duplicates(subset=['학정번호', '요일', '교시'])
    if not df.empty:
        df['time_slots_set'] = df.apply(lambda r: set((r['요일'], int(p)) for p in r['교시'].split(',')), axis=1)
    return df


# --- [UI/UX] 요즘 대학생 취향의 깔끔한 Pretendard 폰트 및 모던 네이비 스타일 ---
st.set_page_config(page_title="YONSEI GS-ED Timetable", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;800&display=swap');
        * { font-family: 'Pretendard', sans-serif !important; }
        
        .main-title { font-size: 2.2rem; font-weight: 800; color: #112F6F; margin-bottom: 5px; }
        .sub-title { font-size: 1rem; color: #64748B; margin-bottom: 25px; }
        
        .card { background-color: #F8FAFC; padding: 18px; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 12px; }
        .course-list-item { padding: 12px; background-color: #F1F5F9; border-radius: 10px; margin-bottom: 8px; border-left: 5px solid #112F6F; }
        
        .stTabs [data-baseweb="tab"] { font-weight: 600; color: #64748B; font-size: 15px; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #112F6F !important; border-bottom-color: #112F6F !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🦅 YONSEI GS-ED</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">연세대학교 교육대학원 수강신청 시간표 도우미 (2025-2)</div>', unsafe_allow_html=True)

PREDEFINED_COLORS = ["#E2EFFE", "#FEE2E2", "#FEF3C7", "#E0F2FE", "#ECEFEE", "#F3E8FF", "#ECFDF5", "#FFF1F2", "#F0FDFA", "#EFF6FF"]


# ==========================================
#  📦 SIDEBAR: 파일 수동 업로드 패널 추가
# ==========================================
with st.sidebar:
    st.markdown("### 📊 시간표 파일 등록")
    # 사용자가 직접 엑셀 파일을 드래그 앤 드롭 하도록 유도
    uploaded_file = st.file_uploader(
        "교대원 시간표 엑셀 파일(.xls, .xlsx)을 업로드해 주세요.", 
        type=["xls", "xlsx"]
    )
    st.write("---")

# 파일이 업로드되었을 경우에만 데이터를 가져오고, 안 올라왔으면 화면 잠금(안내 메시지)
if uploaded_file is not None:
    master_df = load_and_parse_yonsei_excel(uploaded_file)
else:
    st.info("📊 서비스를 시작하려면 왼쪽 사이드바에 연세대학교 교육대학원 시간표 엑셀 파일(`.xls` 또는 `.xlsx`)을 업로드해 주세요.")
    st.stop()  # 파일이 들어오기 전까지 하단 로직 실행 차단

if master_df.empty:
    st.error("⚠️ 데이터를 파싱하지 못했습니다. 올바른 형식의 연세교대원 시간표 엑셀 파일이 맞는지 다시 확인해 주세요.")
    st.stop()


# 상태 관리 변수 초기화
if 'my_courses' not in st.session_state: st.session_state.my_courses = []
if 'color_map' not in st.session_state: st.session_state.color_map = {}

# --- [경고 완벽 해결] st.query_params 최신 문법 리팩토링 ---
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
        for key in list(st.query_params.keys()):
            del st.query_params[key]

# 중복 및 공강 시간 자동 필터링 엔진
def get_available_courses(df, selected_ids):
    if not selected_ids: return df
    available_df = df[~df['학정번호'].isin(selected_ids)]
    my_busy_slots = set().union(*df[df['학정번호'].isin(selected_ids)]['time_slots_set'])
    return available_df[available_df['time_slots_set'].apply(lambda s: s.isdisjoint(my_busy_slots))]

available_df = get_available_courses(master_df, st.session_state.my_courses)


# ==========================================
#  LAYOUT SIDEBAR: 에타 감성의 통합 검색창 & 필터 기본 동작
# ==========================================
with st.sidebar:
    st.markdown("### 🛠️ 강좌 검색 및 필터 패널")
    search_query = st.text_input("🔎 과목명 또는 교수명 검색", placeholder="예: 학습과학 또는 이희승...").strip().lower()
    st.write("---")
    
    tab_m, tab_k = st.tabs(["🎓 전공 강좌 조회", "🍎 교직/공통 조회"])
    
    # 1) 전공 강좌 탭 파트
    with tab_m:
        major_list = sorted([m for m in master_df['전공'].unique() if "교직" not in m and "평생" not in m])
        if major_list:
            selected_major = st.selectbox("소속 전공 선택", major_list)
            filtered_major = available_df[available_df['전공'] == selected_major]
            if search_query:
                filtered_major = filtered_major[filtered_major['과목명'].str.lower().str.contains(search_query) | filtered_major['교수명'].str.lower().str.contains(search_query)]
                
            if not filtered_major.empty:
                sel_idx = st.selectbox("과목 선택", options=filtered_major.index, 
                                       format_func=lambda idx: f"[{filtered_major.loc[idx]['요일']}] {filtered_major.loc[idx]['과목명']} - {filtered_major.loc[idx]['교수명']}")
                if st.button("➕ 시간표에 전공 추가", use_container_width=True, type="primary"):
                    row = filtered_major.loc[sel_idx]
                    st.session_state.my_courses.append(row['학정번호'])
                    st.session_state.color_map[row['과목명']] = PREDEFINED_COLORS[len(st.session_state.color_map) % len(PREDEFINED_COLORS)]
                    st.query_params["courses"] = ",".join(st.session_state.my_courses)
                    st.rerun()
            else:
                st.caption("현재 추가 가능한 전공 과목이 없습니다.")
        else:
            st.caption("조회된 전공이 없습니다.")

    # 2) 교직 강좌 탭 파트
    with tab_k:
        kyojik_type = st.selectbox("교직/공통 분류", ["전체", "교직(공통)", "교직(자격증)", "평생교육사"])
        filtered_k = available_df[available_df['전공'].str.contains("교직|평생")]
        if kyojik_type != "전체":
            filtered_k = filtered_k[filtered_k['전공'] == kyojik_type]
        if search_query:
            filtered_k = filtered_k[filtered_k['과목명'].str.lower().str.contains(search_query) | filtered_k['교수명'].str.lower().str.contains(search_query)]
            
        if not filtered_k.empty:
            sel_idx_k = st.selectbox("과목 선택 ", options=filtered_k.index, 
                                     format_func=lambda idx: f"[{filtered_k.loc[idx]['요일']}] {filtered_k.loc[idx]['과목명']} - {filtered_k.loc[idx]['교수명']}")
            if st.button("➕ 시간표에 교직 추가", use_container_width=True, type="primary"):
                row = filtered_k.loc[sel_idx_k]
                st.session_state.my_courses.append(row['학정번호'])
                st.session_state.color_map[row['과목명']] = PREDEFINED_COLORS[len(st.session_state.color_map) % len(PREDEFINED_COLORS)]
                st.query_params["courses"] = ",".join(st.session_state.my_courses)
                st.rerun()
        else:
            st.caption("현재 추가 가능한 교직 과목이 없습니다.")

# ==========================================
#  LAYOUT MAIN: 시각화 시간표 보드 & 장바구니 리스트
# ==========================================
if not st.session_state.my_courses:
    st.info("💡 왼쪽 사이드바에서 소속 전공이나 교직 과목을 선택하시면, 엑셀에서 파싱된 실시간 강좌 리스트가 나타납니다!")
else:
    my_df = master_df[master_df['학정번호'].isin(st.session_state.my_courses)].drop_duplicates(subset=['학정번호'])
    total_credits = my_df['학점'].sum()
    
    col_a, col_b = st.columns([0.75, 0.25])
    with col_a:
        st.markdown(f"### 🗓️ MY TIMETABLE `[ 총 {len(my_df)} 과목 / {total_credits} 학점 이수 ]`")
    with col_b:
        if st.button("🗑️ 전체 초기화", use_container_width=True):
            st.session_state.my_courses, st.session_state.color_map = [], {}
            for key in list(st.query_params.keys()):
                del st.query_params[key]
            st.rerun()

    # 타임라인 테이블 마크업
    days = ['월', '화', '수', '목', '금']
    periods = [1, 2, 3, 4]
    time_labels = {1: "1교시<br><small>18:20-19:10</small>", 2: "2교시<br><small>19:15-20:05</small>", 3: "3교시<br><small>20:10-21:00</small>", 4: "4교시<br><small>21:05-21:55</small>"}
    grid = {(p, d): {"text": "", "color": "#FFFFFF", "span": 1, "visible": True} for p in periods for d in days}
    
    # 선택된 연세교대원 과목들 그리드 매핑 연산
    for _, row in master_df[master_df['학정번호'].isin(st.session_state.my_courses)].iterrows():
        color = st.session_state.color_map.get(row['과목명'], "#FFFFFF")
        p_list = sorted([int(p) for p in row['교시'].split(',')])
        if len(p_list) == 2 and p_list[1] == p_list[0] + 1:
            grid[(p_list[0], row['요일'])] = {
                "text": f"<div style='font-weight:700; color:#1E293B; font-size:13px;'>{row['과목명']}</div><div style='font-size:11px; margin-top:4px; color:#64748B;'>{row['교수명']} · {row['강의실']}</div>",
                "color": color, "span": 2, "visible": True
            }
            grid[(p_list[1], row['요일'])]["visible"] = False
        else:
            for p in p_list:
                grid[(p, row['요일'])] = {
                    "text": f"<div style='font-weight:700; color:#1E293B; font-size:13px;'>{row['과목명']}</div><div style='font-size:11px; margin-top:4px; color:#64748B;'>{row['교수명']} · {row['강의실']}</div>",
                    "color": color, "span": 1, "visible": True
                }

    table_html = """
    <div id="capture-area" style="padding: 10px; background: #ffffff; border-radius: 16px;">
    <table style="width:100%; border-collapse:separate; border-spacing: 6px; text-align:center; table-layout:fixed;">
        <thead>
            <tr style="height:40px; background-color:#F1F5F9;">
                <th style="border-radius:8px; color:#475569; font-size:12px; font-weight:600; width:13%;">TIME</th>
    """
    for d in days:
        table_html += f'<th style="border-radius:8px; color:#475569; font-size:13px; font-weight:600;">{d}요일</th>'
    table_html += '</tr></thead><tbody>'
    
    for p in periods:
        table_html += f'<tr style="height:85px;"><td style="background-color:#F8FAFC; border-radius:8px; color:#64748B; font-size:11px; font-weight:600; padding:5px; line-height:1.4;">{time_labels[p]}</td>'
        for d in days:
            cell = grid[(p, d)]
            if cell["visible"]:
                bg = cell["color"]
                border_radius = "border-radius: 10px;" if cell["text"] else "border-radius: 10px; background-color:#F8FAFC; border: 1px dashed #E2E8F0;"
                table_html += f'<td rowspan="{cell["span"]}" style="{border_radius} background-color:{bg}; padding:10px;">{cell["text"]}</td>'
        table_html += '</tr>'
    table_html += '</tbody></table></div>'

    js_downloader = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <button id="download-btn" style="width:100%; margin-top:15px; padding:12px; background-color:#112F6F; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:600; font-size:14px;">✨ 감성 시간표 이미지 저장하기</button>
    <div id="status-log" style="margin-top:6px; font-size:12px; text-align:center;"></div>
    <script>
        document.getElementById('download-btn').onclick = function() {
            const area = document.getElementById("capture-area");
            const log = document.getElementById('status-log');
            log.innerText = '이미지 제작 중...'; log.style.color = '#112F6F';
            html2canvas(area, {scale: 3, backgroundColor: '#ffffff', borderRadius: 16}).then(canvas => {
                const a = document.createElement("a");
                a.href = canvas.toDataURL("image/png");
                a.download = "YONSEI_TIMETABLE.png";
                document.body.appendChild(a); a.click(); document.body.removeChild(a);
                log.innerText = '✅ 다운로드 폴더에 안전하게 저장되었습니다!'; log.style.color = '#059669';
            }).catch(e => { log.innerText = '❌ 에러: ' + e; log.style.color = '#DC2626'; });
        };
    </script>
    """
    st.components.v1.html(table_html + js_downloader, height=480)
    
    st.write("---")
    st.markdown("#### 📝 확정된 장바구니 강좌 상세 내역")
    
    for idx, row in my_df.iterrows():
        st.markdown(f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="background-color:#E0F2FE; color:#0369A1; padding:3px 8px; border-radius:6px; font-size:11px; font-weight:600; margin-right:8px;">{row['과목종별']}</span>
                    <strong style="font-size:15px; color:#1E293B;">{row['과목명']}</strong>
                    <span style="font-size:13px; color:#64748B; margin-left:10px;">| {row['교수명']} 교수님 · {row['강의실']} ({row['요일']}요일 {row['교시']}교시)</span>
                </div>
                <div style="font-size:12px; color:#94A3B8;">학정번호: {row['학정번호']} ({row['학점']}학점)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("과목 제외", key=f"del-{row['학정번호']}", type="secondary"):
            st.session_state.my_courses.remove(row['학정번호'])
            if st.session_state.my_courses:
                st.query_params["courses"] = ",".join(st.session_state.my_courses)
            else:
                for key in list(st.query_params.keys()):
                    del st.query_params[key]
            st.rerun()
