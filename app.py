import streamlit as st
import pandas as pd
import os
import re

# --- 1. 파일 분석 및 년도/학기 동적 추출 함수 ---
def detect_year_semester(file_path):
    """
    파일명과 엑셀 내용에서 년도와 학기를 자동으로 추출합니다.
    기본값은 현재 기준으로 설정하되, 파일에서 발견되면 해당 값으로 변경합니다.
    """
    year = "2026"
    semester = "1학기"
    
    # 1. 파일명에서 추출 시도 (예: time_table1(2025-2).xlsx -> 2025년 2학기)
    base_name = os.path.basename(file_path)
    match_file = re.search(r'(\d{4})[-_](\d)', base_name)
    if match_file:
        year = match_file.group(1)
        semester = f"{match_file.group(2)}학기"
        return year, semester

    # 2. 파일명에 정보가 없을 경우 엑셀 상단 텍스트 검색 (안전장치)
    try:
        df_check = pd.read_excel(file_path, nrows=5, header=None)
        for col in df_check.columns:
            for val in df_check[col].dropna().astype(str):
                match_content = re.search(r'(\d{4})학년도\s*(\d)학기', val)
                if match_content:
                    year = match_content.group(1)
                    semester = f"{match_content.group(2)}학기"
                    return year, semester
    except:
        pass
        
    return year, semester

# --- 2. 연대 교대원 전용 엑셀 파서 (Raw 데이터 변환) ---
def parse_yonsei_graduate_excel(file_path):
    """
    연세대 교육대학원 특유의 세로 나열형 정형/비정형 엑셀을 
    Streamlit에서 검색 및 필터링이 가능한 클린 데이터프레임으로 변환합니다.
    """
    try:
        # openpyxl 엔진을 사용하여 로드
        df_raw = pd.read_excel(file_path, header=None)
    except Exception as e:
        st.error(f"엑셀 파일을 읽는 중 오류가 발생했습니다: {e}")
        return None

    all_courses = []
    current_major = "공통/교직" # 기본 섹션명
    
    # 행별로 순회하며 구조 파싱
    row_idx = 0
    total_rows = len(df_raw)
    
    while row_idx < total_rows:
        row_vals = df_raw.iloc[row_idx].dropna().tolist()
        row_str = " ".join([str(x) for x in row_vals])
        
        # 1. 전공 섹션 타이틀 감지 (예: "평생교육경영 .... 주임교수 : OOO")
        if "주임교수" in row_str or "시각디자인교육" in row_str or "조리교육" in row_str:
            # 첫 번째 셀이나 주요 텍스트를 전공명으로 저장
            for val in row_vals:
                if "주임교수" unknowns_removed := val.split(":")[0].strip():
                    current_major = re.sub(r'\s+', '', unknowns_removed).replace("구분", "").strip()
                    break
            row_idx += 1
            continue
            
        # 2. 요일 헤더 행 스킵 ("구분", "월", "화", "목" 등)
        if "구      분" in row_str or "구분" in row_str:
            row_idx += 1
            continue
            
        # 3. 교시 및 시간 블록 감지
        first_cell = str(df_raw.iloc[row_idx, 0]) if pd.notna(df_raw.iloc[row_idx, 0]) else ""
        if "교시" in first_cell or "동영상" in first_cell:
            time_slot_text = first_cell # 예: "-1교시\n동영상\n\n1,2교시\n오후\n6:20\n~\n8:00"
            
            # 해당 교시 블록 아래에 붙어있는 과목 데이터들 수집 (다음 교시나 전공이 나오기 전까지)
            sub_row = row_idx + 1
            
            # 데이터 수집을 위한 임시 딕셔너리 리스트 (컬럼별 배치 대응)
            # 연대 교대원 양식은 가로로 월/화/목 요일별 데이터가 배치됨
            days_headers = []
            header_row = df_raw.iloc[row_idx - 1] if row_idx > 0 else []
            
            # 현재 시간 블록의 가로 컬럼 매핑 정보 확인 (월, 화, 수, 목, 금, 토)
            day_cols = {}
            for col_c in range(1, len(df_raw.columns)):
                # 위쪽 행들을 보며 요일 텍스트 찾기
                for lookup_r in range(max(0, row_idx-2), row_idx):
                    val_lookup = str(df_raw.iloc[lookup_r, col_c])
                    for d in ['월', '화', '수', '목', '금', '토']:
                        if d in val_lookup and len(val_lookup.strip()) <= 2:
                            day_cols[col_c] = d
            
            # 과목 정보 파싱 바이트 생성
            course_blocks = {} # col_idx -> {info}
            
            while sub_row < total_rows:
                next_first_cell = str(df_raw.iloc[sub_row, 0]) if pd.notna(df_raw.iloc[sub_row, 0]) else ""
                next_row_str = " ".join([str(x) for x in df_raw.iloc[sub_row].dropna().tolist()])
                
                # 다음 블록을 만나면 정지
                if "교시" in next_first_cell or "주임교수" in next_row_str or "구      분" in next_first_cell:
                    break
                    
                label_cell = str(df_raw.iloc[sub_row, 1]) if pd.notna(df_raw.iloc[sub_row, 1]) else ""
                
                # 키-밸류 특성 추출
                for c_idx in day_cols.keys():
                    val = df_raw.iloc[sub_row, c_idx]
                    if pd.notna(val) and str(val).strip():
                        if c_idx not in course_blocks:
                            course_blocks[c_idx] = {"요일": day_cols[c_idx], "시간텍스트": time_slot_text}
                        
                        clean_label = label_cell.replace(" ", "").strip()
                        if "과목종별" in clean_label or "종별" in clean_label:
                            course_blocks[c_idx]["이수구분"] = str(val).strip()
                        elif "학정번호" in clean_label or "코드" in clean_label:
                            course_blocks[c_idx]["교과목코드"] = str(val).strip()
                        elif "과목명" in clean_label:
                            course_blocks[c_idx]["교과목명"] = str(val).strip()
                        elif "교수명" in clean_label:
                            course_blocks[c_idx]["교수명"] = str(val).strip()
                        elif "강의실" in clean_label:
                            course_blocks[c_idx]["강의실"] = str(val).strip()
                            
                sub_row += 1
            
            # 수집된 과목 블록들 마스터 리스트에 추가
            for c_idx, c_data in course_blocks.items():
                if "교과목명" in c_data and "교과목코드" in c_data:
                    # 학점 기본값 세팅 (일반적으로 대학원 과목은 2~3학점, 논문지도 등은 2학점)
                    c_data["학점"] = 2
                    if "논문" in c_data["교과목명"]:
                        c_data["이수구분"] = "논문/연구"
                    
                    c_data["전공분류"] = current_major
                    c_data["분반"] = 1
                    
                    # 학정번호 뒤에 분반이 붙어있는 경우 분리 (예: SGS6695-01 -> 코드: SGS6695, 분반: 1)
                    code_raw = c_data["교과목코드"]
                    if "-" in code_raw:
                        parts = code_raw.split("-")
                        c_data["교과목코드"] = parts[0]
                        try:
                            c_data["분반"] = int(parts[1])
                        except:
                            pass
                            
                    all_courses.append(c_data)
                    
            row_idx = sub_row
            continue
            
        row_idx += 1

    df_result = pd.DataFrame(all_courses)
    
    # 정형 구조 확보를 위한 빈 컬럼 방어 코드
    for col in ["교과목명", "교수명", "학점", "이수구분", "전공분류", "분반", "강의실", "교과목코드", "요일", "시간텍스트"]:
        if col not in df_result.columns:
            df_result[col] = ""
            
    # 정교한 시간표 배치용 데이터 파싱 로직 추가
    def calculate_slots(row):
        slots = set()
        day = row['요일']
        time_text = row['시간텍스트']
        
        if not day or not time_text:
            return slots
            
        # 교시 번호 추출 (예: "1,2교시" -> [1, 2], "3,4교시" -> [3, 4])
        # 야간 교시 매핑 보정
        periods = [int(x) for x in re.findall(r'(\d+)\s*교시', time_text)]
        
        # 만약 "1,2교시" 형태가 매칭되지 않고 텍스트 내에 숫자가 있으면 연속된 시간으로 매핑
        if not periods:
            digit_find = [int(x) for x in re.findall(r'\d+', time_text.split("오후")[0])]
            if digit_find:
                periods = digit_find
                
        # 매핑용 표준 정수 변환
        for p in periods:
            slots.add((day, p))
        return slots

    if not df_result.empty:
        df_result['time_slots_set'] = df_result.apply(calculate_slots, axis=1)
    else:
        df_result['time_slots_set'] = [set() for _ in range(len(df_result))]
        
    return df_result


# --- 3. Streamlit 앱 메인 UI 설정 ---

# 엑셀 파일 경로 탐색 (현재 디렉토리 내 모든 xls/xlsx 파일 대상 자동 타겟팅)
excel_files = [f for f in os.listdir('.') if f.endswith(('.xls', '.xlsx'))]
excel_file_path = excel_files[0] if excel_files else 'time_table1(2025-2).xls'

# 파일 존재 여부에 따른 년도/학기 동적 변경 적용
if os.path.exists(excel_file_path):
    target_year, target_semester = detect_year_semester(excel_file_path)
else:
    target_year, target_semester = "2025", "2학기" # 파일 부재시 폴백 가이드라인

st.set_page_config(page_title=f"연세대학교 교육대학원 시간표 도우미", layout="wide")
st.title(f"🦅 연세대학교 교육대학원 [{target_year}학년도 {target_semester}] 시간표 도우미")

st.markdown(f"📂 현재 분석 및 연동된 파일: `{excel_file_path}` (시스템이 해당 년도를 자동 인식함)")

# --- 주요 기능 안내 바 ---
with st.expander("✨ 주요 기능 및 사용 안내 (클릭하여 확인)"):
    st.info(
        f"""
        * **{target_year}학년도 {target_semester} 파일 완벽 맞춤형**: 사용자가 업로드한 엑셀 파일의 서식을 AI 파서가 파싱하여 학정번호, 과목명, 야간 교시를 분리해 냅니다.
        * **실시간 중복 검사**: 시간대나 과목코드가 겹치면 리스트에서 실시간 제외됩니다.
        * **🔗 URL 실시간 공유**: 주소창의 링크를 복사해 원우들에게 넘기면 내가 조합한 시간표를 그대로 전송할 수 있습니다.
        """
    )

# --- 데이터 전처리 가동 ---
if not os.path.exists(excel_file_path):
    st.error(f"📌 폴더 내에 엑셀 파일이 없습니다. 파일명을 `{excel_file_path}`로 바꾸어 넣어주세요.")
    st.stop()

master_df = parse_yonsei_graduate_excel(excel_file_path)

# --- 색상 테마 테이블 ---
PREDEFINED_COLORS = [
    "#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3", "#fdb462",
    "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd", "#ccebc5", "#ffed6f"
]

if master_df is not None and not master_df.empty:
    if 'my_courses' not in st.session_state: st.session_state.my_courses = []
    if 'color_map' not in st.session_state: st.session_state.color_map = {}

    # URL 공유 파라미터 복원 기능
    if "courses" in st.query_params and not st.session_state.my_courses:
        try:
            courses_str = st.query_params.get("courses")
            if courses_str:
                shared_courses = []
                for item in courses_str.split(','):
                    if '-' in item:
                        code, no = item.split('-')
                        no = int(no)
                        if not master_df[(master_df['교과목코드'] == code) & (master_df['분반'] == no)].empty:
                            shared_courses.append((code, no))
                if shared_courses:
                    st.session_state.my_courses = shared_courses
                    for _, row in master_df[master_df.set_index(['교과목코드', '분반']).index.isin(shared_courses)].iterrows():
                        if row['교과목명'] not in st.session_state.color_map:
                            st.session_state.color_map[row['교과목명']] = PREDEFINED_COLORS[len(st.session_state.color_map) % len(PREDEFINED_COLORS)]
                    st.rerun()
        except:
            st.query_params.clear()

    # 중복 과목 및 시간대 충돌 과목 필터링 함수
    def get_available_courses(df, selected_list):
        if not selected_list: return df
        selected_codes = {c for c, n in selected_list}
        # 1. 과목 중복 제거
        avail = df[~df['교과목코드'].isin(selected_codes)]
        # 2. 시간대 중복 제거
        chosen_df = df[df.set_index(['교과목코드', '분반']).index.isin(selected_list)]
        busy_slots = set().union(*chosen_df['time_slots_set']) if not chosen_df.empty else set()
        if busy_slots:
            avail = avail[avail['time_slots_set'].apply(lambda s: s.isdisjoint(busy_slots))]
        return avail

    available_df = get_available_courses(master_df, st.session_state.my_courses)

    # --- UI 1. 필터링 및 검색 ---
    st.subheader("🔍 1. 전공 및 교과목 검색")
    col1, col2 = st.columns(2)
    with col1:
        majors = ["전체"] + sorted(master_df['전공분류'].unique().tolist())
        selected_major = st.selectbox("세부 전공 필터", majors)
    with col2:
        types = ["전체"] + sorted(master_df['이수구분'].unique().tolist())
        selected_type = st.selectbox("이수 구분 필터", types)

    filtered_df = available_df.copy()
    if selected_major != "전체":
        filtered_df = filtered_df[filtered_df['전공분류'] == selected_major]
    if selected_type != "전체":
        filtered_df = filtered_df[filtered_df['이수구분'] == selected_type]

    search_q = st.text_input("🔎 과목명 또는 교수명 검색 키워드 입력")
    if search_q:
        filtered_df = filtered_df[
            filtered_df['교과목명'].str.contains(search_q, case=False, na=False) |
            filtered_df['교수명'].str.contains(search_q, case=False, na=False)
        ]

    # 과목 선택 및 추가
    if filtered_df.empty:
        st.warning("선택 조건에 맞는 수강 가능 강좌가 없습니다.")
    else:
        def fmt_str(r):
            time_lbl = r['시간텍스트'].replace('\n', ' ')
            return f"[{r['전공분류']} / {r['이수구분']}] {r['교과목명']} ({r['교수명']}, {r['강의실'] or '강의실미정'}) | {time_lbl}"

        selected_idx = st.selectbox("추가할 강좌 선택", filtered_df.index, format_func=lambda x: fmt_str(filtered_df.loc[x]))
        
        if st.button("🔥 내 시간표에 담기", use_container_width=True):
            tgt = filtered_df.loc[selected_idx]
            pair = (tgt['교과목코드'], tgt['분반'])
            st.session_state.my_courses.append(pair)
            if tgt['교과목명'] not in st.session_state.color_map:
                st.session_state.color_map[tgt['교과목명']] = PREDEFINED_COLORS[len(st.session_state.color_map) % len(PREDEFINED_COLORS)]
            st.query_params["courses"] = ",".join([f"{c}-{n}" for c, n in st.session_state.my_courses])
            st.success(f"✅ '{tgt['교과목명']}' 추가 완료!")
            st.rerun()

    st.divider()

    # --- UI 2. 시간표 프리뷰 시각화 ---
    st.subheader("📅 2. 내 타임 테이블 (Preview)")
    
    if not st.session_state.my_courses:
        st.info("좌측 대시보드에서 과목을 선택하시면 시간표 격자가 동적으로 시각화됩니다.")
    else:
        my_df = master_df[master_df.set_index(['교과목코드', '분반']).index.isin(st.session_state.my_courses)]
        
        # 요일 및 교시 격자 정의 (연대 교대원 야간 수업 표준 포맷팅)
        days_to_show = ['월', '화', '수', '목', '금']
        periods_to_show = [1, 2, 3, 4, 5, 6, 7] # 1~4주간, 5~7야간교시
        
        time_labels = {
            1: "1교시<br>(09:00~10:00)", 2: "2교시<br>(10:00~12:00)", 
            3: "3교시<br>(12:00~14:00)", 4: "4교시<br>(14:00~16:00)",
            5: "야간 1,2교시<br>(18:20~20:00)", 6: "야간 3,4교시<br>(20:10~21:50)",
            7: "야간 5,6교시<br>(21:55~22:45)"
        }

        # 렌더링용 매트릭스 빌드
        grid = {(p, d): {"text": "", "color": "white"} for p in periods_to_show for d in days_to_show}
        
        for _, r in my_df.iterrows():
            color = st.session_state.color_map.get(r['교과목명'], "white")
            cell_text = f"<b>{r['교과목명']}</b><br><span style='font-size:0.9em;'>{r['교수명']}<br>({r['강의실'] or '미정'})</span>"
            for (d, p) in r['time_slots_set']:
                if (p, d) in grid:
                    grid[(p, d)] = {"text": cell_text, "color": color}

        # HTML 그리기
        col_w = 90 / len(days_to_show)
        th_html = "".join([f"<th width='{col_w}%'>{d}요일</th>" for d in days_to_show])
        
        tr_html = ""
        for p in periods_to_show:
            tr_html += f"<tr><td class='time-header'><b>{time_labels[p]}</b></td>"
            for d in days_to_show:
                cell = grid[(p, d)]
                tr_html += f"<td style='background-color:{cell['color']};'>{cell['text']}</td>"
            tr_html += "</tr>"

        html_code = f"""
        <style>
            .tt-table {{ width:100%; border-collapse:collapse; table-layout:fixed; font-family:-apple-system,sans-serif; }}
            .tt-table th, .tt-table td {{ border:1px solid #dbe2ef; text-align:center; vertical-align:middle; padding:8px; height:75px; font-size:13px; word-break:keep-all; }}
            .tt-table th {{ background-color:#002060; color:white; font-weight:bold; }}
            .time-header {{ background-color:#f8f9fa; font-size:11px; color:#495057; }}
            .download-btn {{ background-color:#002060; color:white; padding:10px 20px; border:none; border-radius:4px; font-weight:bold; cursor:pointer; margin-top:10px; }}
        </style>
        <div id='timetable-area'>
            <table class='tt-table'>
                <tr><th width='10%'>시간</th>{th_html}</tr>
                {tr_html}
            </table>
        </div>
        """
        st.components.v1.html(html_code, height=620)

        # 아래쪽 선택 리스트 및 초기화 관리
        st.write("---")
        l_col, r_col = st.columns([0.8, 0.2])
        with l_col:
            st.markdown(f"#### 📝 담은 과목 총 개수: **{len(my_df)}**개")
        with r_col:
            if st.button("🔄 시간표 전체 초기화", type="primary"):
                st.session_state.my_courses = []
                st.session_state.color_map = {}
                st.query_params.clear()
                st.rerun()

        for idx, (code, no) in enumerate(st.session_state.my_courses):
            match_rows = master_df[(master_df['교과목코드'] == code) & (master_df['분반'] == no)]
            if match_rows.empty: continue
            c = match_rows.iloc[0]
            c_col, d_col = st.columns([0.85, 0.15])
            with c_col:
                st.markdown(f"""
                <div style="padding:8px 12px; border-left:5px solid {st.session_state.color_map.get(c['교과목명'],'#ccc')}; background-color:#f1f3f5; margin-bottom:4px; font-size:14px;">
                    <strong>[{c['전공분류']}] {c['교과목명']}</strong> - {c['교수명']} ({c['교과목코드']}-{c['분반']:02d}) | {c['시간텍스트'].replace('\n',' ')}
                </div>
                """, unsafe_allow_html=True)
            with d_col:
                if st.button("제거", key=f"del-{code}-{no}-{idx}", use_container_width=True):
                    st.session_state.my_courses.pop(idx)
                    up = ",".join([f"{cc}-{nn}" for cc, nn in st.session_state.my_courses])
                    if up: st.query_params["courses"] = up
                    else: st.query_params.clear()
                    st.rerun()
else:
    st.warning("⚠️ 엑셀 파일 파싱 결과 데이터가 비어있거나 올바른 구조가 아닙니다. 행과 열 배치를 확인해 주세요.")
