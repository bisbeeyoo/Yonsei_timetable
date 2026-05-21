import streamlit as st
import pandas as pd

# --- [UI 개선] 메인 페이지 레이아웃 및 트렌디한 스타일 커스텀 ---
st.set_page_config(page_title="YONSEI GS-ED Timetable", layout="wide", initial_sidebar_state="expanded")

# 요즘 대학생들이 선호하는 깔끔한 미니멀리즘 + 네이비 포인트 CSS 적용
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;800&display=swap');
        
        * { font-family: 'Pretendard', sans-serif !important; }
        
        /* 메인 타이틀 스타일 */
        .main-title {
            font-size: 2.2rem; font-weight: 800; color: #112F6F; margin-bottom: 5px;
        }
        .sub-title {
            font-size: 1rem; color: #666; margin-bottom: 25px;
        }
        
        /* 카드형 보드 스타일 */
        .card {
            background-color: #F8FAFC; padding: 20px; border-radius: 12px;
            border: 1px solid #E2E8F0; margin-bottom: 15px;
        }
        
        /* 탭 가독성 개선 */
        .stTabs [data-baseweb="tab"] {
            font-weight: 600; color: #64748B; font-size: 15px;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #112F6F !important; border-bottom-color: #112F6F !important;
        }
        
        /* 제거 버튼 미니멀화 */
        .stButton>button {
            border-radius: 8px; transition: all 0.2s;
        }
    </style>
""", unsafe_allow_html=True)

# 메인 헤더 배너
st.markdown('<div class="main-title">🦅 YONSEI GS-ED</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">연세대학교 교육대학원 수강신청 시간표 시뮬레이터 (2025-2)</div>', unsafe_allow_html=True)

# --- 색상 팔레트 (요즘 유행하는 차분한 파스텔 톤) ---
PREDEFINED_COLORS = [
    "#E2EFFE", "#FEE2E2", "#FEF3C7", "#E0F2FE", "#ECEFEE", 
    "#F3E8FF", "#ECFDF5", "#FFF1F2", "#F0FDFA", "#EFF6FF"
]

# --- 데이터셋 로드 (제공된 CSV 기반 정제 데이터) ---
@st.cache_data
def load_yonsei_data():
    raw_data = [
        # 교직일반, 논문, 교직이론 및 교직소양
        {"전공": "교직(공통)", "요일": "월", "교시": "1,2", "과목종별": "교직", "학정번호": "SPG6824-01", "과목명": "한국교육의 역사", "교수명": "이원재", "강의실": "교302", "학점": 3}, [cite: 1]
        {"전공": "교직(공통)", "요일": "화", "교시": "1,2", "과목종별": "교직", "학정번호": "SPG6858-01", "과목명": "교사의인식및실천연구(영어)", "교수명": "임웅", "강의실": "교304", "학점": 3}, [cite: 1]
        {"전공": "교직(공통)", "요일": "화", "교시": "1,2", "과목종별": "교직", "학정번호": "SPG6862-01", "과목명": "학습과학", "교수명": "이희승", "강의실": "교310", "학점": 3}, [cite: 1]
        {"전공": "교직(공통)", "요일": "목", "교시": "1,2", "과목종별": "교직", "학정번호": "SPG6867-01", "과목명": "교육자를위한인공지능입문", "교수명": "강근영", "강의실": "교302", "학점": 3}, [cite: 1]
        {"전공": "교직(공통)", "요일": "월", "교시": "3,4", "과목종별": "교직", "학정번호": "SPG6860-01", "과목명": "연세와교사의사명", "교수명": "곽호철", "강의실": "교603", "학점": 3}, [cite: 1]
        {"전공": "교직(공통)", "요일": "월", "교시": "3,4", "과목종별": "교직", "학정번호": "SPG6869-01", "과목명": "교육현장을위한문학읽기", "교수명": "곽수범", "강의실": "교601", "학점": 3}, [cite: 1, 2]
        {"전공": "교직(공통)", "요일": "화", "교시": "3,4", "과목종별": "교직", "학정번호": "SPG6864-01", "과목명": "박물관교육", "교수명": "국성하", "강의실": "교405", "학점": 3}, [cite: 1]
        {"전공": "교직(공통)", "요일": "화", "교시": "3,4", "과목종별": "교직", "학정번호": "SPG6838-01", "과목명": "교육과일의세계", "교수명": "한수정", "강의실": "교302", "학점": 3}, [cite: 1, 2]
        {"전공": "교직(공통)", "요일": "화", "교시": "3,4", "과목종별": "교직", "학정번호": "SPG6859-01", "과목명": "인공지능시대의과학기술과교육(영어)", "교수명": "임웅", "강의실": "교304", "학점": 3}, [cite: 2]
        {"전공": "교직(공통)", "요일": "화", "교시": "3,4", "과목종별": "교직", "학정번호": "SPG6853-01", "과목명": "학습동기", "교수명": "김은주", "강의실": "위204", "학점": 3}, [cite: 2]
        {"전공": "교직(공통)", "요일": "화", "교시": "3,4", "과목종별": "교직", "학정번호": "SPG6831-01", "과목명": "영재교육의이론과실제", "교수명": "윤성로", "강의실": "교306", "학점": 3}, [cite: 2]
        {"전공": "교직(공통)", "요일": "목", "교시": "3,4", "과목종별": "교직", "학정번호": "SPG6863-01", "과목명": "교사론", "교수명": "국성하", "강의실": "교404", "학점": 3}, [cite: 1]
        {"전공": "교직(공통)", "요일": "목", "교시": "3,4", "과목종별": "교직", "학정번호": "SPG6868-01", "과목명": "교육자를위한인공지능과코딩기초(영어)", "교수명": "한수연", "강의실": "교304", "학점": 3}, [cite: 1, 2]
        
        # 교직이론 및 교직소양 (1,2교시)
        {"전공": "교직(자격증)", "요일": "월", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6662-01", "과목명": "교육철학및교육사", "교수명": "황금중", "강의실": "교404", "학점": 2}, [cite: 3]
        {"전공": "교직(자격증)", "요일": "월", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6644-01", "과목명": "교육사회학", "교수명": "김영미", "강의실": "교306", "학점": 2}, [cite: 3]
        {"전공": "교직(자격증)", "요일": "월", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6668-01", "과목명": "교직실무", "교수명": "심연식", "강의실": "교303", "학점": 2}, [cite: 3]
        {"전공": "교직(자격증)", "요일": "월", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6661-01", "과목명": "교육행정및교육경영", "교수명": "유동훈", "강의실": "교308", "학점": 2}, [cite: 3]
        {"전공": "교직(자격증)", "요일": "화", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6643-02", "과목명": "교육심리학", "교수명": "원영실", "강의실": "교410", "학점": 2}, [cite: 3]
        {"전공": "교직(자격증)", "요일": "화", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6663-02", "과목명": "교육방법및교육공학", "교수명": "김은주", "강의실": "교405", "학점": 2}, [cite: 3]
        {"전공": "교직(자격증)", "요일": "화", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6662-03", "과목명": "교육철학및교육사", "교수명": "국성하", "강의실": "교404", "학점": 2}, [cite: 3]
        {"전공": "교직(자격증)", "요일": "화", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6664-01", "과목명": "교육과정", "교수명": "양은배", "강의실": "백S408", "학점": 2}, [cite: 3]
        {"전공": "교직(자격증)", "요일": "화", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6659-02", "과목명": "교육학개론", "교수명": "이원재", "강의실": "교303", "학점": 2}, [cite: 3, 4]
        {"전공": "교직(자격증)", "요일": "화", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6666-01", "과목명": "생활지도및상담", "교수명": "양승민", "강의실": "교402", "학점": 2}, [cite: 4]
        {"전공": "교직(자격증)", "요일": "화", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6668-03", "과목명": "교직실무", "교수명": "신명미", "강의실": "교101", "학점": 2}, [cite: 4]
        {"전공": "교직(자격증)", "요일": "화", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6667-01", "과목명": "특수교육학개론", "교수명": "윤성로", "강의실": "교306", "학점": 2}, [cite: 4]
        {"전공": "교직(자격증)", "요일": "목", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6667-02", "과목명": "특수교육학개론", "교수명": "김지영", "강의실": "교303", "학점": 2}, [cite: 3]
        {"전공": "교직(자격증)", "요일": "목", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6645-03", "과목명": "학교폭력예방및학생의이해", "교수명": "류부열", "강의실": "교404", "학점": 2}, [cite: 3]
        {"전공": "교직(자격증)", "요일": "목", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6665-01", "과목명": "교육평가", "교수명": "김주아", "강의실": "교402", "학점": 2}, [cite: 3]
        {"전공": "교직(자격증)", "요일": "목", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6658-01", "과목명": "교육실습", "교수명": "국성하", "강의실": "교410", "학점": 2}, [cite: 3]
        {"전공": "교직(자격증)", "요일": "목", "교시": "1,2", "과목종별": "교직", "학정번호": "SPT6672-01", "과목명": "디지털교육", "교수명": "장은실", "강의실": "교405", "학점": 2}, [cite: 3, 4]
        
        # 교직이론 및 교직소양 (3,4교시)
        {"전공": "교직(자격증)", "요일": "월", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6662-02", "과목명": "교육철학및교육사", "교수명": "국성하", "강의실": "교404", "학점": 2}, [cite: 5]
        {"전공": "교직(자격증)", "요일": "월", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6645-01", "과목명": "학교폭력예방및학생의이해", "교수명": "서정기", "강의실": "교302", "학점": 2}, [cite: 5]
        {"전공": "교직(자격증)", "요일": "월", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6659-01", "과목명": "교육학개론", "교수명": "한수정", "강의실": "교405", "학점": 2}, [cite: 5]
        {"전공": "교직(자격증)", "요일": "월", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6663-01", "과목명": "교육방법및교육공학", "교수명": "신소영", "강의실": "교402", "학점": 2}, [cite: 6]
        {"전공": "교직(자격증)", "요일": "월", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6643-01", "과목명": "교육심리학", "교수명": "김정민", "강의실": "교410", "학점": 2}, [cite: 6]
        {"전공": "교직(자격증)", "요일": "월", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6668-02", "과목명": "교직실무", "교수명": "심연식", "강의실": "교303", "학점": 2}, [cite: 6]
        {"전공": "교직(자격증)", "요일": "월", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6661-02", "과목명": "교육행정및교육경영", "교수명": "유동훈", "강의실": "교306", "학점": 2}, [cite: 6]
        {"전공": "교직(자격증)", "요일": "화", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6643-03", "과목명": "교육심리학", "교수명": "원영실", "강의실": "교410", "학점": 2}, [cite: 5]
        {"전공": "교직(자격증)", "요일": "화", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6645-02", "과목명": "학교폭력예방및학생의이해", "교수명": "서정기", "강의실": "교101", "학점": 2}, [cite: 5]
        {"전공": "교직(자격증)", "요일": "화", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6659-03", "과목명": "교육학개론", "교수명": "이원재", "강의실": "교303", "학점": 2}, [cite: 5]
        {"전공": "교직(자격증)", "요일": "화", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6664-02", "과목명": "교육과정", "교수명": "함영기", "강의실": "교404", "학점": 2}, [cite: 6]
        {"전공": "교직(자격증)", "요일": "화", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6666-02", "과목명": "생활지도및상담", "교수명": "양승민", "강의실": "교402", "학점": 2}, [cite: 6]
        {"전공": "교직(자격증)", "요일": "화", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6668-05", "과목명": "교직실무", "교수명": "곽수범", "강의실": "위203호", "학점": 2}, [cite: 6]
        {"전공": "교직(자격증)", "요일": "목", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6667-03", "과목명": "특수교육학개론", "교수명": "김지영", "강의실": "교303", "학점": 2}, [cite: 5]
        {"전공": "교직(자격증)", "요일": "목", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6665-02", "과목명": "교육평가", "교수명": "김주아", "강의실": "교402", "학점": 2}, [cite: 5]
        {"전공": "교직(자격증)", "요일": "목", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6672-02", "과목명": "디지털교육", "교수명": "장은실", "강의실": "교405", "학점": 2}, [cite: 5]
        {"전공": "교직(자격증)", "요일": "목", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6668-04", "과목명": "교직실무", "교수명": "심연식", "강의실": "교303", "학점": 2}, [cite: 6]
        {"전공": "교직(자격증)", "요일": "목", "교시": "3,4", "과목종별": "교직", "학정번호": "SPT6644-02", "과목명": "교육사회학", "교수명": "김영미", "강의실": "교404", "학점": 2}, [cite: 6]
        
        # 평생교육사
        {"전공": "평생교육사", "요일": "수", "교시": "1,2", "과목종별": "교직", "학정번호": "SPL6691", "과목명": "평생교육프로그램개발론", "교수명": "최유연", "강의실": "교402", "학점": 3}, [cite: 7]
        {"전공": "평생교육사", "요일": "수", "교시": "1,2", "과목종별": "교직", "학정번호": "SPL6650", "과목명": "평생교육론", "교수명": "이상오", "강의실": "교404", "학점": 3}, [cite: 7]
        {"전공": "평생교육사", "요일": "수", "교시": "1,2", "과목종별": "교직", "학정번호": "SPL6684", "과목명": "평생교육경영론", "교수명": "신경석", "강의실": "교405", "학점": 3}, [cite: 7]
        {"전공": "평생교육사", "요일": "금", "교시": "1,2", "과목종별": "교직", "학정번호": "SPL6692", "과목명": "평생교육실습", "교수명": "한수정", "강의실": "교404", "학점": 3}, [cite: 7]
        {"전공": "평생교육사", "요일": "금", "교시": "1,2", "과목종별": "교직", "학정번호": "SPL6690", "과목명": "평생교육방법론", "교수명": "임현민", "강의실": "교402", "학점": 3}, [cite: 7]

        # 교육공학
        {"전공": "교육공학", "요일": "월", "교시": "1,2", "과목종별": "전공", "학정번호": "SET6602-01", "과목명": "교수학습이론", "교수명": "이명근", "강의실": "교606", "학점": 3}, [cite: 8]
        {"전공": "교육공학", "요일": "화", "교시": "1,2", "과목종별": "전공", "학정번호": "SET6608-01", "과목명": "AI교육공학기초", "교수명": "김남주", "강의실": "교606", "학점": 3}, [cite: 8]
        {"전공": "교육공학", "요일": "목", "교시": "1,2", "과목종별": "선택", "학정번호": "SET6652-01", "과목명": "원격교육론", "교수명": "이지영", "강의실": "교606", "학점": 3}, [cite: 8]
        {"전공": "교육공학", "요일": "월", "교시": "3,4", "과목종별": "선택", "학정번호": "SET6678-01", "과목명": "교육공학연구자료분석", "교수명": "박종화", "강의실": "교606", "학점": 3}, [cite: 8]
        {"전공": "교육공학", "요일": "화", "교시": "3,4", "과목종별": "선택", "학정번호": "SET6673-01", "과목명": "기업교육공학연구", "교수명": "백평구", "강의실": "교606", "학점": 3}, [cite: 8]

        # 조기영어교육
        {"전공": "조기영어교육", "요일": "월", "교시": "1,2", "과목종별": "선택", "학정번호": "SEC6711-01", "과목명": "조기영어교육과통계학", "교수명": "이민진", "강의실": "백S404", "학점": 3}, [cite: 22]
        {"전공": "조기영어교육", "요일": "화", "교시": "1,2", "과목종별": "전공", "학정번호": "SEC6701-01", "과목명": "조기영어교육연구방법론", "교수명": "이희경", "강의실": "교517", "학점": 3}, [cite: 22]
        {"전공": "조기영어교육", "요일": "목", "교시": "1,2", "과목종별": "전공", "학정번호": "SEC6606-01", "과목명": "영어학개론", "교수명": "김현우", "강의실": "백S204", "학점": 3}, [cite: 22]
        {"전공": "조기영어교육", "요일": "화", "교시": "3,4", "과목종별": "전공", "학정번호": "SEC6602-01", "과목명": "음성음운론과영어발음교육", "교수명": "이석재", "강의실": "외326-1", "학점": 3}, [cite: 22, 23]
        {"전공": "조기영어교육", "요일": "목", "교시": "3,4", "과목종별": "교직", "학정번호": "SEC6694-01", "과목명": "영어교육학특강", "교수명": "이명신", "강의실": "백S204", "학점": 3}, [cite: 22]

        # AI융합교육
        {"전공": "AI융합교육", "요일": "월", "교시": "1,2", "과목종별": "선택", "학정번호": "SAE6521-01", "과목명": "빅데이터와교육", "교수명": "한수연", "강의실": "교517", "학점": 3}, [cite: 26, 27]
        {"전공": "AI융합교육", "요일": "화", "교시": "1,2", "과목종별": "선택", "학정번호": "SAE6527-01", "과목명": "AI활용융합교육방법", "교수명": "한수연", "강의실": "교603", "학점": 3}, [cite: 26, 27]
        {"전공": "AI융합교육", "요일": "월", "교시": "3,4", "과목종별": "선택", "학정번호": "SAE6526-01", "과목명": "인공지능기술과윤리", "교수명": "임웅", "강의실": "교517", "학점": 3}, [cite: 27]
        {"전공": "AI융합교육", "요일": "화", "교시": "3,4", "과목종별": "선택", "학정번호": "SAE6525-01", "과목명": "딥러닝입문", "교수명": "박헌우", "강의실": "교614", "학점": 3} [cite: 27]
    ]
    df = pd.DataFrame(raw_data)
    df['time_slots_set'] = df.apply(lambda r: set((r['요일'], int(p)) for p in r['교시'].split(',')), axis=1)
    return df

master_df = load_yonsei_data()

if 'my_courses' not in st.session_state: st.session_state.my_courses = []
if 'color_map' not in st.session_state: st.session_state.color_map = {}

# --- URL 읽기 및 상태 동기화 ---
if "courses" in st.query_params and not st.session_state.my_courses:
    try:
        courses_str = st.query_params.get("courses")
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
        st.query_params.clear()

# --- 중복 방지 실시간 필터 시스템 ---
def get_available_courses(df, selected_ids):
    if not selected_ids: return df
    available_df = df[~df['학정번호'].isin(selected_ids)]
    my_busy_slots = set().union(*df[df['학정번호'].isin(selected_ids)]['time_slots_set'])
    return available_df[available_df['time_slots_set'].apply(lambda s: s.isdisjoint(my_busy_slots))]

available_df = get_available_courses(master_df, st.session_state.my_courses)

# ==========================================
#  LAYOUT: 요즘 유행하는 2단 대시보드 레이아웃 (사이드바 필터 + 메인 타임라인)
# ==========================================

# 1. 사이드바 (컨트롤 패널 - 여기서 다 골라요!)
with st.sidebar:
    st.markdown("### 🛠️ 강좌 필터링 패널")
    
    search_query = st.text_input("🔎 과목명 또는 교수명 검색", placeholder="검색어 입력...").strip().lower()
    
    st.write("---")
    
    tab_m, tab_k = st.tabs(["🎓 전공 강좌", "🍎 교직/공통"])
    
    # 전공 탭 조회
    with tab_m:
        major_list = sorted([m for m in master_df['전공'].unique() if "교직" not in m and "평생" not in m])
        selected_major = st.selectbox("전공학과", major_list)
        
        filtered_major = available_df[available_df['전공'] == selected_major]
        if search_query:
            filtered_major = filtered_major[filtered_major['과목명'].str.lower().str.contains(search_query) | filtered_major['교수명'].str.lower().str.contains(search_query)]
            
        if not filtered_major.empty:
            sel_idx = st.selectbox("강좌 선택", options=filtered_major.index, format_func=lambda idx: f"{filtered_major.loc[idx]['과목명']} ({filtered_major.loc[idx]['교수명']})")
            if st.button("➕ 전공 추가", use_container_width=True, type="primary"):
                row = filtered_major.loc[sel_idx]
                st.session_state.my_courses.append(row['학정번호'])
                st.session_state.color_map[row['과목명']] = PREDEFINED_COLORS[len(st.session_state.color_map) % len(PREDEFINED_COLORS)]
                st.query_params["courses"] = ",".join(st.session_state.my_courses)
                st.rerun()
        else:
            st.caption("선택 가능한 전공 과목이 없습니다.")

    # 교직 탭 조회
    with tab_k:
        kyojik_type = st.selectbox("교직구분", ["전체", "교직(공통)", "교직(자격증)", "평생교육사"])
        filtered_k = available_df[available_df['전공'].str.contains("교직|평생")]
        if kyojik_type != "전체":
            filtered_k = filtered_k[filtered_k['전공'] == kyojik_type]
        if search_query:
            filtered_k = filtered_k[filtered_k['과목명'].str.lower().str.contains(search_query) | filtered_k['교수명'].str.lower().str.contains(search_query)]
            
        if not filtered_k.empty:
            sel_idx_k = st.selectbox("강좌 선택", options=filtered_k.index, format_func=lambda idx: f"{filtered_k.loc[idx]['과목명']} ({filtered_k.loc[idx]['교수명']})")
            if st.button("➕ 교직 추가", use_container_width=True, type="primary"):
                row = filtered_k.loc[sel_idx_k]
                st.session_state.my_courses.append(row['학정번호'])
                st.session_state.color_map[row['과목명']] = PREDEFINED_COLORS[len(st.session_state.color_map) % len(PREDEFINED_COLORS)]
                st.query_params["courses"] = ",".join(st.session_state.my_courses)
                st.rerun()
        else:
            st.caption("선택 가능한 교직 과목이 없습니다.")

# 2. 메인 화면 (나의 트렌디 시간표 시각화)
if not st.session_state.my_courses:
    st.info("💡 왼쪽 사이드바 패널에서 과목을 선택해 추가하면 실시간으로 감성적인 시간표 보드가 완성됩니다!")
else:
    my_df = master_df[master_df['학정번호'].isin(st.session_state.my_courses)]
    total_credits = my_df['학점'].sum()
    
    # 학점 요약 뱃지 리포트 디자인
    col_a, col_b = st.columns([0.75, 0.25])
    with col_a:
        st.markdown(f"### 🗓️ MY TIMETABLE `[ 총 {len(my_df)} 과목 / {total_credits} 학점 이수 중 ]`")
    with col_b:
        if st.button("🗑️ 전체 초기화", use_container_width=True):
            st.session_state.my_courses, st.session_state.color_map = [], {}
            st.query_params.clear()
            st.rerun()

    # --- HTML / CSS 기반 인스타 감성 낭낭한 미니멀 시간표 뷰포트 ---
    days = ['월', '화', '수', '목', '금']
    periods = [1, 2, 3, 4]
    time_labels = {1: "1교시<br><small>18:20-19:10</small>", 2: "2교시<br><small>19:15-20:05</small>", 3: "3교시<br><small>20:10-21:00</small>", 4: "4교시<br><small>21:05-21:55</small>"}
    
    grid = {(p, d): {"text": "", "color": "#FFFFFF", "span": 1, "visible": True} for p in periods for d in days}
    
    for _, row in my_df.iterrows():
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

    # 고급 테이블 스타일링 마크업 언어 주입
    table_html = """
    <div id="capture-area" style="padding: 10px; background: #ffffff; border-radius: 16px;">
    <table style="width:100%; border-collapse:separate; border-spacing: 6px; text-align:center; table-layout:fixed;">
        <thead>
            <tr style="height:40px; background-color:#F1F5F9;">
                <th style="border-radius:8px; color:#475569; font-size:12px; font-weight:600; width:13%;">TIME</th>
    """
    for d in days:
        table_html += f'<th style="border-radius:8px; color:#475569; font-size:13px; font-weight:600;">{d}</th>'
    table_html += '</tr></thead><tbody>'
    
    for p in periods:
        table_html += f'<tr style="height:85px;"><td style="background-color:#F8FAFC; border-radius:8px; color:#64748B; font-size:11px; font-weight:600; padding:5px; line-height:1.4;">{time_labels[p]}</td>'
        for d in days:
            cell = grid[(p, d)]
            if cell["visible"]:
                bg = cell["color"]
                border_radius = "border-radius: 10px;" if cell["text"] else "border-radius: 10px; background-color:#F8FAFC; border: 1px dashed #E2E8F0;"
                table_html += f'<td rowspan="{cell["span"]}" style="{border_radius} background-color:{bg}; padding:10px; transition:all 0.2s;">{cell["text"]}</td>'
        table_html += '</tr>'
    table_html += '</tbody></table></div>'

    # 이미지 전환용 모던 스크립트 결합 다운로더 
    js_downloader = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <button id="download-btn" style="width:100%; margin-top:15px; padding:12px; background-color:#112F6F; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:600; font-size:14px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">✨ 인스타 감성 시간표 이미지 저장하기</button>
    <div id="status-log" style="margin-top:6px; font-size:12px; text-align:center;"></div>
    <script>
        document.getElementById('download-btn').onclick = function() {
            const area = document.getElementById("capture-area");
            const log = document.getElementById('status-log');
            log.innerText = '이미지 빌드 중...'; log.style.color = '#112F6F';
            html2canvas(area, {scale: 3, backgroundColor: '#ffffff', borderRadius: 16}).then(canvas => {
                const a = document.createElement("a");
                a.href = canvas.toDataURL("image/png");
                a.download = "YONSEI_TIMETABLE.png";
                document.body.appendChild(a); a.click(); document.body.removeChild(a);
                log.innerText = '✅ 갤러리에 저장되었습니다!'; log.style.color = '#059669';
            }).catch(e => { log.innerText = '❌ 에러: ' + e; log.style.color = '#DC2626'; });
        };
    </script>
    """
    st.components.v1.html(table_html + js_downloader, height=480)
    
    st.write("---")
    st.markdown("#### 📝 담아둔 장바구니 상세 리스트")
    
    # 리스트 카드로 예쁘게 정렬
    for idx, row in my_df.iterrows():
        with st.container():
            st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="background-color:#E0F2FE; color:#0369A1; padding:3px 8px; border-radius:6px; font-size:11px; font-weight:600; margin-right:8px;">{row['과목종별']}</span>
                        <strong style="font-size:15px; color:#1E293B;">{row['과목명']}</strong>
                        <span style="font-size:13px; color:#64748B; margin-left:10px;">| {row['교수명']} 교수님 · {row['강의실']}</span>
                    </div>
                    <div style="font-size:12px; color:#94A3B8;">학정번호: {row['학정번호']} ({row['학점']}학점)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 카드의 우측 정렬을 유지하기 위해 별도 처리한 삭제 액션 버튼
            if st.button("과목 제외", key=f"del-{row['학정번호']}", type="secondary"):
                st.session_state.my_courses.remove(row['학정번호'])
                if st.session_state.my_courses:
                    st.query_params["courses"] = ",".join(st.session_state.my_courses)
                else:
                    st.query_params.clear()
                st.rerun()
