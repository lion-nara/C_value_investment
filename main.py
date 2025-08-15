import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os

st.set_page_config(page_title="가치주 분석 커뮤니티", page_icon="📈", layout="wide",
                   initial_sidebar_state="expanded")

# ---------- CSS ----------
st.markdown("""      
<style>
    .main { background-color: #1e3a5f; color: white; }
    .company-card {
        background-color: #f5f5dc; color:#333; padding:15px; border-radius:10px;
        margin:10px 0; box-shadow:0 2px 4px rgba(0,0,0,0.1);
    }
    .valuation-buy { color:#dc3545; font-weight:bold; }
    .valuation-sell { color:#007bff; font-weight:bold; }
    .post-card {
        background-color:#f8f9fa; color:#333; padding:15px; border-radius:8px;
        margin:10px 0; border-left:4px solid #007bff;
    }
    /* 버튼형 탭: 서로 바짝 붙도록 gap 최소화 */
    .tab-row { margin: 6px 0 14px 0; }
    .tabbtn > button {
        width: 100%;
        border: 1px solid #e2e8f0;
        background: #ffffff;
        color: #1f2937;
        padding: 10px 14px;
        border-radius: 10px;
        font-weight: 600;
    }
    .tabbtn.active > button {
        background: #0ea5e9;
        color: white;
        border-color: #0ea5e9;
    }
    /* 입력 너비/작성 폼 시인성 개선 */
    .stTextInput input, .stTextArea textarea { width: 100%; }
    .stTextArea textarea { min-height: 220px; }
    
    /* 작성 닫기/새 리서치 버튼을 셀렉트박스 높이에 맞춰 살짝 내려서(여백),
        버튼 자체 높이도 길게 */
    .right-toolbar {
        margin-top: 6px;           /* 위쪽으로 살짝 내림. 필요시 8~12px로 조절 */
    }
    .right-toolbar .stButton > button {
        height: 42px;              /* 기본 ~38px보다 살짝 높게 */
        padding: 8px 14px;         /* 내부 패딩 */
    }
</style>
""", unsafe_allow_html=True)

DATA_FILE = "investment_data.json"
POSTS_FILE = "posts_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return []

def save_posts(posts):
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

def initialize_user_data(username):
    return {
        "username": username,
        "destiny_company": {"name":"","current_price":0,"target_buy":0,"target_sell":0,"description":""},
        "interesting_companies": [
            {"name":"","current_price":0,"target_buy":0,"target_sell":0,"description":""} for _ in range(5)
        ]
    }

# ---- session ----
ss = st.session_state
ss.setdefault("logged_in", False)
ss.setdefault("username", "")
ss.setdefault("selected_company", "")
ss.setdefault("show_research_form", False)
ss.setdefault("active_tab", "📊 내 관심 기업")

TABS = ["📊 내 관심 기업", "📝 리서치 게시글", "⚙️ 기업 정보 수정"]

def login_page():
    st.title("📈 가치주 분석 커뮤니티")
    st.markdown("### 로그인")
    with st.form("login_form"):
        username = st.text_input("사용자명", placeholder="사용자명을 입력하세요")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        if st.form_submit_button("로그인") and username:
            ss.logged_in, ss.username = True, username
            st.rerun()

# ---------- 버튼형 탭 네비게이션 (바짝 붙음) ----------
def render_navbar():
    st.markdown('<div class="tab-row"></div>', unsafe_allow_html=True)
    # gap="small"로 간격 최소화 + 3등분
    c1, c2, c3 = st.columns(3, gap="small")
    for i, (col, name) in enumerate(zip([c1,c2,c3], TABS)):
        with col:
            klass = "tabbtn active" if ss.active_tab == name else "tabbtn"
            st.markdown(f'<div class="{klass}">', unsafe_allow_html=True)
            if st.button(name, key=f"tabbtn_{i}", use_container_width=True):
                ss.active_tab = name
                ss.show_research_form = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

def main_dashboard():
    data = load_data()
    if ss.username not in data:
        data[ss.username] = initialize_user_data(ss.username)
        save_data(data)
    user_data = data[ss.username]

    # 헤더: 로그아웃을 우측 끝이 아니라 '조금 안쪽'으로 끌어오기 (3열: 제목 / 여백 / 버튼)
    h1, spacer, h2 = st.columns([6, 1, 2], gap="small")
    with h1:
        st.title(f"📈 {ss.username}님의 투자 대시보드")
    with h2:
        # 우측 정렬 느낌 유지
        st.write("")  # vertical spacer
        if st.button("로그아웃", use_container_width=True):
            ss.logged_in = False
            ss.username = ""
            st.rerun()

    render_navbar()

    if ss.active_tab == "📊 내 관심 기업":
        display_companies(user_data)
    elif ss.active_tab == "📝 리서치 게시글":
        research_posts()
    else:
        edit_companies(user_data, data)

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
        st.markdown(f"""
        <div class="company-card">
            <h4>🏢 {company['name']}</h4>
            <p><strong>현재가:</strong> {company['current_price']:,}원</p>
            <p><span class="valuation-buy">매수 목표: {company['target_buy']:,}원</span> |
               <span class="valuation-sell">매도 목표: {company['target_sell']:,}원</span></p>
            <p><strong>특징:</strong> {company['description']}</p>
        </div>
        """, unsafe_allow_html=True)

        btn_key = f"research_{'destiny' if is_destiny else f'company_{company_index}'}_{company['name']}"
        if st.button(f"📝 {company['name']} 리서치 작성", key=btn_key):
            ss.selected_company = company['name']
            ss.show_research_form = True
            ss.active_tab = "📝 리서치 게시글"
            st.rerun()

# ---------- 리서치 게시글 ----------
def research_posts():
    posts = load_posts()
    st.markdown("### 📝 리서치 게시글")

    all_companies = sorted(list({p.get('company','') for p in posts if p.get('company')}))

    # 상단 바: 왼쪽 공간 넉넉(필터/작성폼 라벨 등), 오른쪽은 '작성 닫기/새 리서치'를 로그아웃과 동일 우측 정렬
    left, right = st.columns([7, 2], gap="small")
    with left:
        st.selectbox("기업 선택", ["전체"] + all_companies, key="company_filter")
    with right:
        # 👉 CSS로 높이/정렬 제어할 래퍼
        st.markdown('<div class="right-toolbar">', unsafe_allow_html=True)
        if ss.get('show_research_form', False):
            st.button("작성 닫기", key="close_write_btn",
                    use_container_width=True, on_click=_close_write_form)
        else:
            st.button("새 리서치 작성", key="open_write_btn",
                    use_container_width=True, on_click=_open_write_form)
        st.markdown('</div>', unsafe_allow_html=True)


    # 작성 폼 (넓게)
    if ss.get('show_research_form', False):
        write_research_post(posts)

    selected_company = st.session_state.get("company_filter", "전체")
    filtered = posts if selected_company == "전체" else [p for p in posts if p.get('company') == selected_company]
    filtered.sort(key=lambda x: x.get('timestamp',''), reverse=True)

    for i, post in enumerate(filtered):
        display_post(post, i)

def _open_write_form():
    st.session_state.show_research_form = True

def _close_write_form():
    st.session_state.show_research_form = False
    st.session_state.selected_company = ""

def write_research_post(posts):
    st.markdown("### ✍️ 새 리서치 작성")
    with st.form("research_form", clear_on_submit=True):
        company = st.text_input("기업명", value=st.session_state.get('selected_company',''))
        content = st.text_area("리서치 내용", height=200, max_chars=1000)
        is_public = st.checkbox("공개 설정", value=True)
        submit = st.form_submit_button("게시하기")

        if submit and company and content:
            new_post = {
                "id": len(posts),
                "company": company,
                "content": content,
                "author": st.session_state.username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_public": is_public, "likes": 0, "retweets": 0, "comments": []
            }
            posts.append(new_post)
            save_posts(posts)
            st.session_state.show_research_form = False
            st.session_state.selected_company = company
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

        c1, c2, c3, _ = st.columns([1,1,1,5])
        with c1:
            if st.button(f"❤️ {post['likes']}", key=f"like_{index}"):
                posts = load_posts(); posts[post['id']]['likes'] += 1; save_posts(posts); st.rerun()
        with c2:
            if st.button(f"🔄 {post['retweets']}", key=f"retweet_{index}"):
                posts = load_posts(); posts[post['id']]['retweets'] += 1; save_posts(posts); st.rerun()
        with c3:
            st.write(f"💬 {len(post.get('comments', []))}")

        with st.expander(f"댓글 보기 ({len(post.get('comments', []))})"):
            display_comments(post, index)

def display_comments(post, post_index):
    for c in post.get('comments', []):
        st.markdown(f"""
        <div style="background-color:#e9ecef; padding:8px; margin:5px 0; border-radius:5px;">
            <small><strong>{c['author']}</strong> - {c['timestamp']}</small><br>⤷ {c['content']}
        </div>
        """, unsafe_allow_html=True)
    with st.form(f"comment_form_{post_index}"):
        new_comment = st.text_input("댓글 작성 (최대 140자)", max_chars=140, key=f"comment_input_{post_index}")
        if st.form_submit_button("댓글 달기") and new_comment:
            posts = load_posts()
            posts[post['id']].setdefault('comments', []).append({
                "content": new_comment, "author": st.session_state.username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            save_posts(posts); st.success("댓글이 추가되었습니다!"); st.rerun()

def edit_companies(user_data, data):
    st.markdown("### ⚙️ 기업 정보 관리")
    st.markdown("#### 🎯 Destiny 기업 설정")
    with st.form("destiny_form"):
        d = user_data["destiny_company"]
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("기업명", value=d.get("name",""))
            price = st.number_input("현재가 (원)", value=d.get("current_price",0))
        with c2:
            t_buy = st.number_input("매수 목표가 (원)", value=d.get("target_buy",0))
            t_sell = st.number_input("매도 목표가 (원)", value=d.get("target_sell",0))
        desc = st.text_area("기업 특징", value=d.get("description",""))
        if st.form_submit_button("Destiny 기업 저장"):
            user_data["destiny_company"] = {"name":name,"current_price":price,"target_buy":t_buy,"target_sell":t_sell,"description":desc}
            data[st.session_state.username] = user_data; save_data(data); st.success("Destiny 기업이 저장되었습니다!")

    st.markdown("#### 🔍 관심 기업 5개 설정")
    for i in range(5):
        with st.expander(f"관심 기업 {i+1}"):
            with st.form(f"company_form_{i}"):
                c = user_data["interesting_companies"][i]
                a, b = st.columns(2)
                with a:
                    name = st.text_input("기업명", value=c.get("name",""), key=f"name_{i}")
                    price = st.number_input("현재가 (원)", value=c.get("current_price",0), key=f"price_{i}")
                with b:
                    t_buy = st.number_input("매수 목표가 (원)", value=c.get("target_buy",0), key=f"buy_{i}")
                    t_sell = st.number_input("매도 목표가 (원)", value=c.get("target_sell",0), key=f"sell_{i}")
                desc = st.text_area("기업 특징", value=c.get("description",""), key=f"desc_{i}")
                if st.form_submit_button(f"기업 {i+1} 저장"):
                    user_data["interesting_companies"][i] = {"name":name,"current_price":price,"target_buy":t_buy,"target_sell":t_sell,"description":desc}
                    data[st.session_state.username] = user_data; save_data(data); st.success(f"관심 기업 {i+1}이 저장되었습니다!")

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()
