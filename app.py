import streamlit as st
import random
import pandas as pd
import time

st.set_page_config(
    page_title="스마트 자리 뽑기 (Smart Seat Picker)",
    page_icon="🪑",
    layout="wide",
    initial_sidebar_state="expanded"
)

def is_adjacent(r1, c1, r2, c2):
    """두 좌석 (r1, c1)과 (r2, c2)가 상하좌우 또는 대각선으로 인접해 있는지 확인합니다."""
    dr = abs(r1 - r2)
    dc = abs(c1 - c2)
    return dr <= 1 and dc <= 1 and not (dr == 0 and dc == 0)

def solve_seating(participants, rows, cols, fixed_rules, isolation_rules):
    """고정/격리 제약조건을 만족하는 무작위 좌석 배치를 계산합니다."""
    capacity = rows * cols
    if len(participants) > capacity:
        return None, f"참여 인원({len(participants)}명)이 전체 좌석 용량({capacity}석)보다 많습니다."

    max_attempts = 1000
    for _ in range(max_attempts):
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        unassigned_people = list(participants)
        free_seats = [{'r': r, 'c': c} for r in range(1, rows + 1) for c in range(1, cols + 1)]

        # 1. Place fixed rules
        for rule in fixed_rules:
            person = rule['person']
            r = rule['row']
            c = rule['col']

            if person in unassigned_people and grid[r - 1][c - 1] is None:
                grid[r - 1][c - 1] = person
                unassigned_people.remove(person)
                free_seats = [s for s in free_seats if not (s['r'] == r and s['c'] == c)]

        # 2. Random shuffle for remaining participants & seats
        random.shuffle(unassigned_people)
        random.shuffle(free_seats)

        for i, person in enumerate(unassigned_people):
            seat = free_seats[i]
            grid[seat['r'] - 1][seat['c'] - 1] = person

        # 3. Validate isolation constraints
        valid_isolation = True
        for p1, p2 in isolation_rules:
            pos1, pos2 = None, None
            for r in range(1, rows + 1):
                for c in range(1, cols + 1):
                    if grid[r - 1][c - 1] == p1:
                        pos1 = (r, c)
                    if grid[r - 1][c - 1] == p2:
                        pos2 = (r, c)

            if pos1 and pos2 and is_adjacent(pos1[0], pos1[1], pos2[0], pos2[1]):
                valid_isolation = False
                break

        if valid_isolation:
            return grid, None

    return None, "격리 조건이 너무 까다로워 조건에 맞는 배치를 찾지 못했습니다. 조건을 완화해 주세요."

if 'fixed_rules' not in st.session_state:
    st.session_state.fixed_rules = []
if 'isolation_rules' not in st.session_state:
    st.session_state.isolation_rules = []
if 'seating_grid' not in st.session_state:
    st.session_state.seating_grid = None
if 'revealed_seats' not in st.session_state:
    st.session_state.revealed_seats = set()

st.title("🪑 스마트 자리 뽑기 (Smart Seat Picker)")
st.caption("공정하고 편리한 Streamlit 기반 인터랙티브 좌석 배치 시스템")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ 배치 및 조건 설정")
    
    # Step 1: Participants Input
    st.subheader("1. 참가자 명단")
    raw_input = st.text_area(
        "참가자 이름을 콤마(,) 또는 줄바꿈으로 입력하세요:",
        value="김철수, 이영희, 박민수, 정수진, 최동현, 강서연, 윤재석, 한지민",
        height=120
    )
    
    participants = [p.strip() for p in raw_input.replace('\n', ',').split(',') if p.strip()]
    st.info(f"총 **{len(participants)}**명 입력됨")
    
    st.markdown("---")
    
    # Step 2: Grid Size
    st.subheader("2. 좌석 그리드 규격")
    col_r, col_c = st.columns(2)
    with col_r:
        rows = st.number_input("행 (Rows)", min_value=1, max_value=15, value=4)
    with col_c:
        cols = st.number_input("열 (Cols)", min_value=1, max_value=15, value=6)
        
    capacity = rows * cols
    if len(participants) > capacity:
        st.error(f"좌석 용량({capacity}석)이 인원수({len(participants)}명)보다 부족합니다.")
    else:
        st.success(f"총 좌석 용량: **{capacity}석**")
        
    st.markdown("---")
    
    # Step 3: Fixed Seat Rule
    st.subheader("3. 특별 조건 설정")
    with st.expander("📌 특정 자리 고정", expanded=False):
        if participants:
            f_person = st.selectbox("고정할 인원", options=["선택하세요"] + participants, key="f_person")
            seat_options = [f"{r}행 {c}열" for r in range(1, rows + 1) for c in range(1, cols + 1)]
            f_seat = st.selectbox("고정할 좌석", options=["선택하세요"] + seat_options, key="f_seat")
            
            if st.button("고정 조건 추가", use_container_width=True):
                if f_person != "선택하세요" and f_seat != "선택하세요":
                    r_val, c_val = map(int, f_seat.replace("행", "").replace("열", "").split())
                    
                    # Duplicate check
                    if any(r['person'] == f_person for r in st.session_state.fixed_rules):
                        st.warning("이미 다른 자리에 고정된 인원입니다.")
                    elif any(r['row'] == r_val and r['col'] == c_val for r in st.session_state.fixed_rules):
                        st.warning("이미 다른 인원이 고정된 좌석입니다.")
                    else:
                        st.session_state.fixed_rules.append({'person': f_person, 'row': r_val, 'col': c_val})
                        st.success(f"{f_person} ➔ {r_val}행 {c_val}열 추가됨")
                        st.rerun()

    # Step 4: Isolation Rule
    with st.expander("🚫 서로 이웃 금지 (격리)", expanded=False):
        if len(participants) >= 2:
            iso_p1 = st.selectbox("인원 A", options=["선택하세요"] + participants, key="iso_p1")
            iso_p2 = st.selectbox("인원 B", options=["선택하세요"] + participants, key="iso_p2")
            
            if st.button("격리 조건 추가", use_container_width=True):
                if iso_p1 != "선택하세요" and iso_p2 != "선택하세요":
                    if iso_p1 == iso_p2:
                        st.warning("서로 다른 두 인원을 선택해야 합니다.")
                    else:
                        rule = tuple(sorted([iso_p1, iso_p2]))
                        if rule not in st.session_state.isolation_rules:
                            st.session_state.isolation_rules.append(rule)
                            st.success(f"{iso_p1} ↔ {iso_p2} 격리 추가됨")
                            st.rerun()

    # Display Active Rules
    if st.session_state.fixed_rules or st.session_state.isolation_rules:
        st.markdown("**설정된 조건 목록:**")
        for idx, rule in enumerate(st.session_state.fixed_rules):
            col_txt, col_del = st.columns([4, 1])
            col_txt.caption(f"📌 {rule['person']} ➔ {rule['row']}행 {rule['col']}열")
            if col_del.button("❌", key=f"del_fix_{idx}"):
                st.session_state.fixed_rules.pop(idx)
                st.rerun()
                
        for idx, (p1, p2) in enumerate(st.session_state.isolation_rules):
            col_txt, col_del = st.columns([4, 1])
            col_txt.caption(f"🚫 {p1} ↔ {p2} 격리")
            if col_del.button("❌", key=f"del_iso_{idx}"):
                st.session_state.isolation_rules.pop(idx)
                st.rerun()
                
    if st.button("🔄 조건 및 배치 초기화", type="secondary", use_container_width=True):
        st.session_state.fixed_rules = []
        st.session_state.isolation_rules = []
        st.session_state.seating_grid = None
        st.session_state.revealed_seats = set()
        st.rerun()

btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 1])

with btn_col1:
    start_draw = st.button("🎲 무작위 자리 추첨 시작", type="primary", use_container_width=True)

with btn_col2:
    reveal_all = st.button("👁️ 전체 자석 공개", use_container_width=True, disabled=(st.session_state.seating_grid is None))

with btn_col3:
    hide_all = st.button("🙈 전체 좌석 가리기", use_container_width=True, disabled=(st.session_state.seating_grid is None))

if start_draw:
    if not participants:
        st.error("참가자 이름을 입력해 주세요.")
    else:
        with st.spinner("최적의 좌석 배치를 계산 중입니다..."):
            time.sleep(0.5) # Animation delay effect
            grid_res, err = solve_seating(
                participants, rows, cols, 
                st.session_state.fixed_rules, 
                st.session_state.isolation_rules
            )
            if err:
                st.error(err)
            else:
                st.session_state.seating_grid = grid_res
                st.session_state.revealed_seats = set() # Hide all cards initially
                st.balloons()
                st.success("자리 추첨이 완료되었습니다! 아래 버튼을 클릭하여 확인하세요.")

if reveal_all and st.session_state.seating_grid:
    all_seats = {(r, c) for r in range(1, rows + 1) for c in range(1, cols + 1)}
    st.session_state.revealed_seats = all_seats

if hide_all and st.session_state.seating_grid:
    st.session_state.revealed_seats = set()

st.markdown("---")

if st.session_state.seating_grid is not None:
    grid = st.session_state.seating_grid

    # Front Blackboard Indicator
    st.markdown(
        """
        <div style="background-color: #1e293b; color: #94a3b8; text-align: center; 
                    padding: 8px; border-radius: 8px; font-weight: bold; margin-bottom: 20px;
                    border: 1px solid #334155;">
            📺 칠판 / 교탁 (FRONT)
        </div>
        """,
        unsafe_allow_html=True
    )

    # Render Interactive Grid Card Buttons
    for r in range(1, rows + 1):
        grid_cols = st.columns(cols)
        for c in range(1, cols + 1):
            with grid_cols[c - 1]:
                person = grid[r - 1][c - 1]
                is_revealed = (r, c) in st.session_state.revealed_seats
                is_fixed = any(rule['row'] == r and rule['col'] == c for rule in st.session_state.fixed_rules)
                
                label = f"❓ {r}-{c}" if not is_revealed else f"{person if person else '빈자리'}"
                if is_revealed and is_fixed:
                    label += " 📌"

                # Button to toggle reveal state
                if st.button(label, key=f"seat_{r}_{c}", use_container_width=True, type="primary" if is_revealed else "secondary"):
                    if is_revealed:
                        st.session_state.revealed_seats.remove((r, c))
                    else:
                        st.session_state.revealed_seats.add((r, c))
                    st.rerun()

    st.markdown("---")

    st.subheader("📋 배치 결과 내보내기")
    
    # DataFrame conversion
    table_data = []
    for r in range(1, rows + 1):
        row_dict = {"행": f"{r}행"}
        for c in range(1, cols + 1):
            person = grid[r - 1][c - 1]
            row_dict[f"{c}열"] = person if person else "-"
        table_data.append(row_dict)

    df = pd.DataFrame(table_data).set_index("행")
    
    tab1, tab2 = st.tabs(["📊 테이블 보기", "📝 텍스트 복사용"])
    
    with tab1:
        st.dataframe(df, use_container_width=True)
        csv_data = df.to_csv().encode('utf-8-sig')
        st.download_button(
            label="📥 CSV 다운로드",
            data=csv_data,
            file_name=f"seating_result_{time.strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
    with tab2:
        text_summary = f"=== 자리 배치 결과 ({rows}행 {cols}열) ===\n\n"
        for r in range(1, rows + 1):
            row_str = f"[{r}행] "
            for c in range(1, cols + 1):
                p = grid[r - 1][c - 1]
                row_str += f"{c}열: {p if p else '빈자리'}\t"
            text_summary += row_str + "\n"
            
        st.code(text_summary, language="text")

else:
    st.info("👈 좌측 사이드바에서 인원 및 그리드를 설정한 후 **[무작위 자리 추첨 시작]** 버튼을 누르세요.")
