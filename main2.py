import streamlit as st
import pandas as pd
import json
import hashlib
from datetime import datetime
import os
import requests
from bs4 import BeautifulSoup
import time

# 페이지 설정
st.set_page_config(
    page_title="가치주 분석 커뮤니티 v2",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main { background-color: #1e3a5f; color: white; }
    .company-card {
        background-color: #f5f5dc; color: #333; padding: 15px; border-radius: 10px;
        margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .valuation-buy { color: #dc3545; font-weight: bold; }
    .valuation-sell { color: #007bff; font-weight: bold; }

    .current-price { font-size: 1.2em; font-weight: bold; color: #28a745; }
    .price-change-up { color: #dc3545; font-weight: bold; }
    .price-change-down { color: #007bff; font-weight: bold; }

    .post-card {
        background-color: #f8f9fa; color: #333; padding: 15px; border-radius: 8px;
        margin: 10px 0; border-left: 4px solid #007bff;
    }
    .reaction-button { background: none; border: none; cursor: pointer; font-size: 14px; margin-right: 10px; }

    .auth-container {
        max-width: 400px; margin: 0 auto; padding: 20px;
        background-color: #f8f9fa; border-radius: 10px; color: #333;
    }

    /* 버튼형 탭: 서로 바짝 붙도록 */
    .tab-row { margin: 6px 0 14px 0; }
    .tabbtn > button {
        width: 100%; border: 1px solid #e2e8f0; background: #ffffff; color: #1f2937;
        padding: 10px 14px; border-radius: 10px; font-weight: 600;
    }
    .tabbtn.active > button { background: #0ea5e9; color: white; border-color: #0ea5e9; }

    /* 리서치 상단 오른쪽 툴바(작성 닫기/새 리서치) 정렬/높이 */
    .right-toolbar { margin-top: 6px; }                 /* 필요시 6~12px로 조정 */
    .right-toolbar .stButton > button { height: 42px; padding: 8px 14px; }

    /* 빠른삽입 버튼 좌측 몰기 + 간격 촘촘 */
    .quickbar { display:flex; gap:8px; flex-wrap:wrap; }
    .quickbar .stButton > button { padding: 6px 12px; }            

    # /* 작성 폼 시인성 */
    # .stTextInput input, .stTextArea textarea { width: 100%; }
    # .stTextArea textarea { min-height: 220px; }
            
</style>
""", unsafe_allow_html=True)

# 데이터 파일 경로 (v2용으로 분리)
DATA_FILE = "investment_data_v2.json"
POSTS_FILE = "posts_data_v2.json"
USERS_FILE = "users_data_v2.json"

# 네이버 증권 주가 크롤링 함수
@st.cache_data(ttl=300)  # 5분 캐시
def get_stock_price(stock_code):
    try:
        url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        current_price = None
        price_element = soup.select_one('.no_today .blind')
        if price_element:
            price_text = price_element.text.strip()
            price_numbers = ''.join(c for c in price_text if c.isdigit() or c == ',')
            if price_numbers:
                current_price = int(price_numbers.replace(',', ''))
        if current_price is None:
            blind_elements = soup.select('.blind')
            for element in blind_elements:
                text = element.text.strip()
                numbers_only = ''.join(c for c in text if c.isdigit() or c == ',')
                if numbers_only and len(numbers_only) >= 3:
                    try:
                        current_price = int(numbers_only.replace(',', ''))
                        break
                    except:
                        continue
        if current_price is None:
            return None

        change = 0
        change_rate = 0.0
        blind_elements = soup.select('.blind')
        for i, element in enumerate(blind_elements):
            text = element.text.strip()
            if i > 0 and i < len(blind_elements) - 1:
                numbers_only = ''.join(c for c in text if c.isdigit() or c == ',')
                if numbers_only and len(numbers_only) <= 6:
                    try:
                        change_value = int(numbers_only.replace(',', ''))
                        if change_value > 0 and change_value < current_price:
                            change = change_value
                            parent_text = str(element.parent) if element.parent else ""
                            if 'minus' in parent_text or 'down' in parent_text.lower():
                                change = -change
                            break
                    except:
                        continue
        for element in blind_elements:
            text = element.text.strip()
            if '%' in text:
                try:
                    rate_text = text.replace('%', '').replace('+', '').replace('-', '').strip()
                    change_rate = float(rate_text)
                    change_rate = -abs(change_rate) if change < 0 else abs(change_rate)
                    break
                except:
                    continue

        return {
            'price': current_price,
            'change': change,
            'change_rate': change_rate,
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except requests.exceptions.RequestException:
        st.error("네트워크 오류: 인터넷 연결을 확인해주세요.")
        return None
    except Exception:
        st.error(f"주가 정보를 가져올 수 없습니다. 주식 코드를 확인해주세요. (코드: {stock_code})")
        return None

# 비밀번호 관련
def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()
def verify_password(password, hashed_password): return hash_password(password) == hashed_password

# 사용자/데이터 로드/저장
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {}
def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f: json.dump(users, f, ensure_ascii=False, indent=2)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {}
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

def load_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return []
def save_posts(posts):
    with open(POSTS_FILE, 'w', encoding='utf-8') as f: json.dump(posts, f, ensure_ascii=False, indent=2)

# 초기 데이터 구조
def initialize_user_data(username):
    return {
        "username": username,
        "destiny_company": {
            "name": "", "stock_code": "", "current_price": 0,
            "target_buy": 0, "target_sell": 0, "description": "", "last_updated": ""
        },
        "interesting_companies": [
            {"name": "", "stock_code": "", "current_price": 0,
             "target_buy": 0, "target_sell": 0, "description": "", "last_updated": ""} for _ in range(5)
        ]
    }

# 세션 상태
ss = st.session_state
ss.setdefault("logged_in_v2", False)
ss.setdefault("username_v2", "")

# 탭/연동 상태 (v2)
ss.setdefault("active_tab_v2", "📊 내 관심 기업")
ss.setdefault("selected_company_v2", "")
ss.setdefault("show_research_form_v2", False)

# 인증 화면
def auth_page():
    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
    st.title("📈 가치주 분석 커뮤니티 v2")
    st.caption("🚀 실시간 주가 연동 + 강화된 보안")
    tab1, tab2 = st.tabs(["🔑 로그인", "👤 회원가입"])
    with tab1: login_form()
    with tab2: signup_form()
    st.markdown("</div>", unsafe_allow_html=True)

def login_form():
    st.markdown("### 로그인")
    users = load_users()
    with st.form("login_form_v2"):
        username = st.text_input("사용자명", placeholder="사용자명을 입력하세요")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        login_button = st.form_submit_button("로그인", use_container_width=True)
        if login_button:
            if username in users and verify_password(password, users[username]['password']):
                ss.logged_in_v2 = True; ss.username_v2 = username
                st.success("로그인 성공!"); time.sleep(1); st.rerun()
            elif username not in users:
                st.error("존재하지 않는 사용자명입니다.")
            else:
                st.error("비밀번호가 올바르지 않습니다.")

def signup_form():
    st.markdown("### 회원가입")
    users = load_users()
    with st.form("signup_form_v2"):
        username = st.text_input("사용자명", placeholder="원하는 사용자명을 입력하세요")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        password_confirm = st.text_input("비밀번호 확인", type="password", placeholder="비밀번호를 다시 입력하세요")
        email = st.text_input("이메일 (선택사항)", placeholder="example@email.com")
        signup_button = st.form_submit_button("회원가입", use_container_width=True)
        if signup_button:
            if not username: st.error("사용자명을 입력해주세요.")
            elif not password: st.error("비밀번호를 입력해주세요.")
            elif password != password_confirm: st.error("비밀번호가 일치하지 않습니다.")
            elif username in users: st.error("이미 존재하는 사용자명입니다.")
            elif len(password) < 4: st.error("비밀번호는 최소 4자 이상이어야 합니다.")
            else:
                users[username] = {
                    'password': hash_password(password),
                    'email': email,
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                save_users(users)
                st.success("회원가입 완료! 로그인 탭에서 로그인해주세요.")

# ----- 버튼형 탭 네비게이션 -----
TABS = ["📊 내 관심 기업", "📝 리서치 게시글", "⚙️ 기업 정보 수정"]
def render_navbar_v2():
    st.markdown('<div class="tab-row"></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="small")
    for i, (col, name) in enumerate(zip([c1, c2, c3], TABS)):
        with col:
            klass = "tabbtn active" if ss.active_tab_v2 == name else "tabbtn"
            st.markdown(f'<div class="{klass}">', unsafe_allow_html=True)
            if st.button(name, key=f"tabbtn_v2_{i}", use_container_width=True):
                ss.active_tab_v2 = name
                ss.show_research_form_v2 = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# 메인 대시보드
def main_dashboard():
    data = load_data()
    if ss.username_v2 not in data:
        data[ss.username_v2] = initialize_user_data(ss.username_v2)
        save_data(data)
    user_data = data[ss.username_v2]

    # 헤더(로그아웃을 우측으로, 살짝 안쪽)
    h1, spacer, h2 = st.columns([6, 1, 2], gap="small")
    with h1: st.title(f"📈 {ss.username_v2}님의 투자 대시보드 v2")
    with h2:
        st.write("")
        if st.button("🔄 주가 업데이트", use_container_width=True):
            update_stock_prices(user_data, data)
            st.success("주가 업데이트 완료!"); st.rerun()
        if st.button("로그아웃", use_container_width=True):
            ss.logged_in_v2 = False; ss.username_v2 = ""; st.rerun()

    # 버튼형 탭바
    render_navbar_v2()

    # 탭 콘텐츠
    if ss.active_tab_v2 == "📊 내 관심 기업":
        display_companies(user_data)
    elif ss.active_tab_v2 == "📝 리서치 게시글":
        research_posts()
    else:
        edit_companies(user_data, data)

# 주가 업데이트
def update_stock_prices(user_data, data):
    if user_data["destiny_company"]["stock_code"]:
        stock_info = get_stock_price(user_data["destiny_company"]["stock_code"])
        if stock_info:
            user_data["destiny_company"]["current_price"] = stock_info['price']
            user_data["destiny_company"]["last_updated"] = stock_info['updated_at']
            user_data["destiny_company"]["change"] = stock_info['change']
            user_data["destiny_company"]["change_rate"] = stock_info['change_rate']
    for company in user_data["interesting_companies"]:
        if company["stock_code"]:
            stock_info = get_stock_price(company["stock_code"])
            if stock_info:
                company["current_price"] = stock_info['price']
                company["last_updated"] = stock_info['updated_at']
                company["change"] = stock_info['change']
                company["change_rate"] = stock_info['change_rate']
    save_data({ss.username_v2: user_data})

# 기업 카드 표시
def display_companies(user_data):
    st.markdown("### 🎯 Destiny 기업")
    destiny = user_data["destiny_company"]
    if destiny["name"]:
        display_company_card(destiny, is_destiny=True)
    else:
        st.info("Destiny 기업을 설정해주세요.")

    st.markdown("### 🔍 관심 기업들")
    for i, company in enumerate(user_data["interesting_companies"]):
        if company["name"]:
            display_company_card(company, company_index=i)

def display_company_card(company, is_destiny=False, company_index=None):
    with st.container():
        # 투자 신호
        investment_signal, signal_color = "", "#333"
        if company.get('current_price', 0) > 0:
            if company['current_price'] <= company.get('target_buy', 0):
                investment_signal, signal_color = "🟢 매수 신호", "#28a745"
            elif company['current_price'] >= company.get('target_sell', 0):
                investment_signal, signal_color = "🔴 매도 신호", "#dc3545"
            else:
                investment_signal, signal_color = "🟡 관망", "#ffc107"

        # 등락
        change_info = ""
        if company.get('change') is not None and company.get('change_rate') is not None:
            change = company['change']; change_rate = company['change_rate']
            if change > 0:
                change_info = f'<span class="price-change-up">▲{change:,}원 (+{change_rate:.2f}%)</span>'
            elif change < 0:
                change_info = f'<span class="price-change-down">▼{abs(change):,}원 ({change_rate:.2f}%)</span>'
            else:
                change_info = f'<span>보합 (0.00%)</span>'

        last_updated_text = f"<small>📅 업데이트: {company.get('last_updated','')}</small>" if company.get('last_updated') else ""

        st.markdown(f"""
        <div class="company-card">
            <h4>🏢 {company['name']}</h4>
            <p>
                <strong>현재가:</strong> {company['current_price']:,}원
                &nbsp;&nbsp;
                <span style="color:{signal_color}; font-weight:bold;">{investment_signal}</span>
            </p>
            <p>
                <span class="valuation-buy">매수 목표: {company['target_buy']:,}원</span> | 
                <span class="valuation-sell">매도 목표: {company['target_sell']:,}원</span>
            </p>
            <p><strong>특징:</strong> {company['description']}</p>
        </div>
        """, unsafe_allow_html=True)

        # 리서치 작성 → 리서치 탭 전환 + 폼 자동 열기 + 회사명 프리필
        btn_key = f"research_v2_{'destiny' if is_destiny else f'company_{company_index}'}_{company['name']}"
        if st.button(f"📝 {company['name']} 리서치 작성", key=btn_key):
            ss.selected_company_v2 = company['name']
            ss.show_research_form_v2 = True
            ss.active_tab_v2 = "📝 리서치 게시글"
            st.rerun()

# 리서치 게시글
def research_posts():
    posts = load_posts()

    # # ── 제목 + 우측 버튼(한 줄) ───────────────────────────
    # h_left, h_right = st.columns([6, 1], gap="small")
    # with h_left:
    #     st.markdown("### 📝 리서치 게시글")
    # with h_right:
    #     st.write("")  # 수직 정렬 미세조정
    #     if ss.get('show_research_form_v2', False):
    #         st.button("작성 닫기", key="close_write_top",
    #                   use_container_width=True, on_click=_close_write_form_v2)
    #     else:
    #         st.button("새 리서치 작성", key="open_write_top",
    #                   use_container_width=True, on_click=_open_write_form_v2)
            
    # ── 제목 + 버튼(제목에 바짝, 한 줄 유지) ──
    c_title, c_btn = st.columns([6,3], gap="small")  # 필요하면 조절
    with c_title:
        st.markdown(
            "<h3 style='margin:0; white-space:nowrap;'>📝 리서치 게시글</h3>",
            unsafe_allow_html=True
        )
    with c_btn:
        st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)  # 수직 정렬 미세조정
        if st.session_state.get('show_research_form_v2', False):
            st.button("작성 닫기", key="close_write_top", on_click=_close_write_form_v2)
        else:
            st.button("새 리서치 작성", key="open_write_top", on_click=_open_write_form_v2)
   


    # ── 상단 필터(버튼은 위로 옮겼으니 여기선 셀렉트만) ──
    all_companies = sorted(list({p.get('company','') for p in posts if p.get('company')}))
    left, _ = st.columns([7, 2], gap="small")
    with left:
        selected_company = st.selectbox("기업 선택", ["전체"] + all_companies,
                                        key="company_filter_v2")

    # ── 작성 폼 열려있으면 표시 ───────────────────────────
    if ss.get('show_research_form_v2', False):
        write_research_post(posts)

    # ── 목록 표시 ─────────────────────────────────────────
    filtered = posts if selected_company == "전체" else [p for p in posts if p.get('company') == selected_company]
    filtered.sort(key=lambda x: x.get('timestamp',''), reverse=True)
    for i, post in enumerate(filtered):
        display_post(post, i)

    export_rows = filtered      # ← 화면에 보이는 목록만. 전체면: posts

    if export_rows:

        # 파일명: 필터가 "전체"면 all, 아니면 회사명 포함 + 타임스탬프
        suffix = "all" if selected_company == "전체" else selected_company
        fname_base = f"research_posts_{suffix}_{datetime.now().strftime('%Y%m%d_%H%M')}".replace(" ", "_")

        # CSV
        df = pd.DataFrame(export_rows)
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")  # 엑셀 한글 깨짐 방지
        st.download_button(
            "📥 (현재 목록) CSV 다운로드",
            data=csv_bytes,
            file_name=f"research_posts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )     
    else:
        st.caption("내보낼 게시글이 없습니다.")
  
def _open_write_form_v2():
    ss.show_research_form_v2 = True

def _close_write_form_v2():
    ss.show_research_form_v2 = False
    ss.selected_company_v2 = ""
    if 'temp_content' in ss: del ss['temp_content']

def write_research_post(posts):
    st.markdown("### ✍️ 새 리서치 작성")
    now = datetime.now()

    with st.form("research_form_v2"):
        company = st.text_input("기업명", value=st.session_state.get('selected_company_v2', ''))

        # 본문(왼쪽) + 날짜 선택(오른쪽)
        left, right = st.columns([3, 1], gap="small")
        with left:
            content = st.text_area(
                "리서치 내용",
                height=180,
                max_chars=2000,
                value=st.session_state.get('temp_content', ''),
                placeholder="리서치 내용을 작성하세요..."
            )
        with right:
            # ✅ CSS 대신 스페이서로 수직 정렬 조정 (원하는 만큼 px 변경)
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            picked_date = st.date_input("날짜 선택", value=now.date(), format="YYYY-MM-DD")
            insert_date = st.form_submit_button("📆 선택 날짜 삽입", use_container_width=True)
            if insert_date:
                date_txt = picked_date.strftime("%Y.%m.%d")
                st.session_state['temp_content'] = f"[{date_txt}] " + st.session_state.get('temp_content', '')
                st.rerun()

        # 빠른 삽입(날짜 없이 텍스트만) — 탭처럼 촘촘/왼쪽 몰기
        st.markdown("**빠른 삽입:**")
        q1, q2, q3, q4 = st.columns(4, gap="small")
        b1 = q1.form_submit_button("📈 분석일", use_container_width=True)
        b2 = q2.form_submit_button("📊 실적 발표", use_container_width=True)
        b3 = q3.form_submit_button("📰 뉴스 정리", use_container_width=True)
        b4 = q4.form_submit_button("🔍 기업 분석", use_container_width=True)

        
        # 클릭 시 텍스트만 추가
        if b1:
            st.session_state['temp_content'] = "분석일\n" + st.session_state.get('temp_content', '')
            st.rerun()
        if b2:
            st.session_state['temp_content'] = "실적 발표\n" + st.session_state.get('temp_content', '')
            st.rerun()
        if b3:
            st.session_state['temp_content'] = "뉴스 정리\n" + st.session_state.get('temp_content', '')
            st.rerun()
        if b4:
            st.session_state['temp_content'] = "기업 분석\n" + st.session_state.get('temp_content', '')
            st.rerun()

        is_public = st.checkbox("공개 설정", value=True)

        c1, c2, c3 = st.columns([1, 1, 1])
        submit = c1.form_submit_button("📝 게시하기", use_container_width=True)
        clear  = c2.form_submit_button("🗑️ 내용 지우기", use_container_width=True)
        cancel = c3.form_submit_button("❌ 취소", use_container_width=True)

        if clear:
            st.session_state.pop('temp_content', None)
            st.rerun()
        if cancel:
            st.session_state.show_research_form_v2 = False
            st.session_state.pop('selected_company_v2', None)
            st.session_state.pop('temp_content', None)
            st.rerun()

        if submit and company and content:
            posts.append({
                "id": len(posts),
                "company": company,
                "content": content,
                "author": st.session_state.username_v2,
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                "is_public": is_public,
                "likes": 0, "retweets": 0, "comments": []
            })
            save_posts(posts)
            st.session_state.show_research_form_v2 = False
            st.session_state.pop('selected_company_v2', None)
            st.session_state.pop('temp_content', None)
            st.success("리서치가 게시되었습니다!")
            st.rerun()


def display_post(post, index):
    with st.container():
        st.markdown(f"""
        <div class="post-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h5>🏢 {post['company']}</h5>
                <small>📅 {post['timestamp']} | 👤 {post['author']}</small>
            </div>
            <p>{post['content']}</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, _ = st.columns([1,1,1,3])
        with col1:
            if st.button(f"❤️ {post['likes']}", key=f"like_v2_{index}"):
                posts = load_posts(); posts[post['id']]['likes'] += 1; save_posts(posts); st.rerun()
        with col2:
            if st.button(f"🔄 {post['retweets']}", key=f"retweet_v2_{index}"):
                posts = load_posts(); posts[post['id']]['retweets'] += 1; save_posts(posts); st.rerun()
        with col3:
            st.write(f"💬 {len(post.get('comments', []))}")

        with st.expander(f"댓글 보기 ({len(post.get('comments', []))})"):
            display_comments(post, index)

def display_comments(post, post_index):
    for i, comment in enumerate(post.get('comments', [])):
        st.markdown(f"""
        <div style="background-color:#e9ecef; padding:8px; margin:5px 0; border-radius:5px;">
            <small><strong>{comment['author']}</strong> - {comment['timestamp']}</small><br>
            ⤷ {comment['content']}
        </div>
        """, unsafe_allow_html=True)

    with st.form(f"comment_form_v2_{post_index}"):
        new_comment = st.text_input("댓글 작성 (최대 140자)", max_chars=140, key=f"comment_input_v2_{post_index}")
        submit_comment = st.form_submit_button("댓글 달기")
        if submit_comment and new_comment:
            posts = load_posts()
            posts[post['id']].setdefault('comments', []).append({
                "content": new_comment, "author": ss.username_v2,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            save_posts(posts); st.success("댓글이 추가되었습니다!"); st.rerun()

# 기업 정보 수정
def edit_companies(user_data, data):
    st.markdown("### ⚙️ 기업 정보 관리")
    st.info("💡 **주식 코드 찾는 방법:** 네이버 증권에서 기업 검색 후 URL의 code= 뒤 6자리 숫자를 입력하세요. (예: 삼성전자 = 005930)")

    st.markdown("#### 🎯 Destiny 기업 설정")
    with st.form("destiny_form_v2"):
        d = user_data["destiny_company"]
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("기업명", value=d.get("name", ""))
            stock_code = st.text_input("주식 코드 (6자리)", value=d.get("stock_code", ""), max_chars=6)
            current_price = st.number_input("현재가 (원)", value=d.get("current_price", 0))
        with col2:
            target_buy = st.number_input("매수 목표가 (원)", value=d.get("target_buy", 0))
            target_sell = st.number_input("매도 목표가 (원)", value=d.get("target_sell", 0))
        description = st.text_area("기업 특징", value=d.get("description", ""))

        c1, c2 = st.columns(2)
        with c1:
            save_button = st.form_submit_button("💾 Destiny 기업 저장", use_container_width=True)
        with c2:
            test_price = st.form_submit_button("🔍 주가 확인", use_container_width=True)
            if test_price and stock_code and len(stock_code) == 6:
                with st.spinner("주가 정보를 가져오는 중..."):
                    stock_info = get_stock_price(stock_code)
                    if stock_info: st.success(f"현재가: {stock_info['price']:,}원")
                    else: st.error("주가 정보를 가져올 수 없습니다. 주식 코드를 확인해주세요.")

        if save_button:
            user_data["destiny_company"] = {
                "name": name, "stock_code": stock_code, "current_price": current_price,
                "target_buy": target_buy, "target_sell": target_sell,
                "description": description, "last_updated": d.get("last_updated", "")
            }
            data[ss.username_v2] = user_data; save_data(data); st.success("Destiny 기업이 저장되었습니다!")

    st.markdown("#### 🔍 관심 기업 5개 설정")
    for i in range(5):
        with st.expander(f"관심 기업 {i+1}"):
            with st.form(f"company_form_v2_{i}"):
                c = user_data["interesting_companies"][i]
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("기업명", value=c.get("name", ""), key=f"name_v2_{i}")
                    stock_code = st.text_input("주식 코드 (6자리)", value=c.get("stock_code", ""), max_chars=6, key=f"code_v2_{i}")
                    current_price = st.number_input("현재가 (원)", value=c.get("current_price", 0), key=f"price_v2_{i}")
                with col2:
                    target_buy = st.number_input("매수 목표가 (원)", value=c.get("target_buy", 0), key=f"buy_v2_{i}")
                    target_sell = st.number_input("매도 목표가 (원)", value=c.get("target_sell", 0), key=f"sell_v2_{i}")
                description = st.text_area("기업 특징", value=c.get("description", ""), key=f"desc_v2_{i}")

                c1, c2 = st.columns(2)
                with c1:
                    save_button = st.form_submit_button(f"💾 기업 {i+1} 저장", use_container_width=True)
                with c2:
                    test_price = st.form_submit_button(f"🔍 주가 확인", use_container_width=True)
                    if test_price and stock_code and len(stock_code) == 6:
                        with st.spinner("주가 정보를 가져오는 중..."):
                            stock_info = get_stock_price(stock_code)
                            if stock_info: st.success(f"현재가: {stock_info['price']:,}원")
                            else: st.error("주가 정보를 가져올 수 없습니다. 주식 코드를 확인해주세요.")

                if save_button:
                    user_data["interesting_companies"][i] = {
                        "name": name, "stock_code": stock_code, "current_price": current_price,
                        "target_buy": target_buy, "target_sell": target_sell,
                        "description": description, "last_updated": c.get("last_updated", "")
                    }
                    data[ss.username_v2] = user_data; save_data(data); st.success(f"관심 기업 {i+1}이 저장되었습니다!")

# 메인
def main():
    if not ss.logged_in_v2:
        auth_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()
