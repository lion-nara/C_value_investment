import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(
    page_title="가치주 분석 커뮤니티",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main {
        background-color: #1e3a5f;
        color: white;
    }
    
    .company-card {
        background-color: #f5f5dc;
        color: #333;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .valuation-buy {
        color: #dc3545;
        font-weight: bold;
    }
    
    .valuation-sell {
        color: #007bff;
        font-weight: bold;
    }
    
    .post-card {
        background-color: #f8f9fa;
        color: #333;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #007bff;
    }
    
    .reaction-button {
        background: none;
        border: none;
        cursor: pointer;
        font-size: 14px;
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 데이터 파일 경로
DATA_FILE = "investment_data.json"
POSTS_FILE = "posts_data.json"

# 데이터 로드 함수
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return []

def save_posts(posts):
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

# 초기 데이터 구조
def initialize_user_data(username):
    return {
        "username": username,
        "destiny_company": {
            "name": "",
            "current_price": 0,
            "target_buy": 0,
            "target_sell": 0,
            "description": ""
        },
        "interesting_companies": [
            {
                "name": "",
                "current_price": 0,
                "target_buy": 0,
                "target_sell": 0,
                "description": ""
            } for _ in range(5)
        ]
    }

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# 로그인 화면
def login_page():
    st.title("📈 가치주 분석 커뮤니티")
    st.markdown("### 로그인")
    
    with st.form("login_form"):
        username = st.text_input("사용자명", placeholder="사용자명을 입력하세요")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        login_button = st.form_submit_button("로그인")
        
        if login_button and username:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()

# 메인 대시보드
def main_dashboard():
    data = load_data()
    
    if st.session_state.username not in data:
        data[st.session_state.username] = initialize_user_data(st.session_state.username)
        save_data(data)
    
    user_data = data[st.session_state.username]
    
    # 헤더
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"📈 {st.session_state.username}님의 투자 대시보드")
    with col2:
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📊 내 관심 기업", "📝 리서치 게시글", "⚙️ 기업 정보 수정"])
    
    with tab1:
        display_companies(user_data)
    
    with tab2:
        research_posts()
    
    with tab3:
        edit_companies(user_data, data)

# 기업 정보 표시
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
            <p>
                <span class="valuation-buy">매수 목표: {company['target_buy']:,}원</span> | 
                <span class="valuation-sell">매도 목표: {company['target_sell']:,}원</span>
            </p>
            <p><strong>특징:</strong> {company['description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 리서치 작성 버튼
        button_key = f"research_{'destiny' if is_destiny else f'company_{company_index}'}_{company['name']}"
        if st.button(f"📝 {company['name']} 리서치 작성", key=button_key):
            st.session_state.selected_company = company['name']
            st.session_state.show_research_form = True

# 리서치 게시글
def research_posts():
    posts = load_posts()
    
    st.markdown("### 📝 리서치 게시글")
    
    # 기업 필터
    all_companies = set()
    for post in posts:
        all_companies.add(post.get('company', ''))
    
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_company = st.selectbox(
            "기업 선택", 
            ["전체"] + sorted(list(all_companies)), 
            key="company_filter"
        )
    
    # 새 리서치 작성
    if st.session_state.get('show_research_form', False):
        write_research_post(posts)
    
    # 게시글 표시
    filtered_posts = posts
    if selected_company != "전체":
        filtered_posts = [post for post in posts if post.get('company') == selected_company]
    
    # 시간순 정렬 (최신순)
    filtered_posts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    for i, post in enumerate(filtered_posts):
        display_post(post, i)

def write_research_post(posts):
    st.markdown("### ✍️ 새 리서치 작성")
    
    with st.form("research_form"):
        company = st.text_input("기업명", value=st.session_state.get('selected_company', ''))
        content = st.text_area("리서치 내용", height=150, max_chars=500)
        is_public = st.checkbox("공개 설정", value=True)
        
        submit = st.form_submit_button("게시하기")
        
        if submit and company and content:
            new_post = {
                "id": len(posts),
                "company": company,
                "content": content,
                "author": st.session_state.username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_public": is_public,
                "likes": 0,
                "retweets": 0,
                "comments": []
            }
            posts.append(new_post)
            save_posts(posts)
            st.session_state.show_research_form = False
            if 'selected_company' in st.session_state:
                del st.session_state.selected_company
            st.success("리서치가 게시되었습니다!")
            st.rerun()

def display_post(post, index):
    with st.container():
        st.markdown(f"""
        <div class="post-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h5>🏢 {post['company']}</h5>
                <small>📅 {post['timestamp']} | 👤 {post['author']}</small>
            </div>
            <p>{post['content']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 반응 버튼들
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
        
        with col1:
            if st.button(f"❤️ {post['likes']}", key=f"like_{index}"):
                posts = load_posts()
                posts[post['id']]['likes'] += 1
                save_posts(posts)
                st.rerun()
        
        with col2:
            if st.button(f"🔄 {post['retweets']}", key=f"retweet_{index}"):
                posts = load_posts()
                posts[post['id']]['retweets'] += 1
                save_posts(posts)
                st.rerun()
        
        with col3:
            comment_count = len(post.get('comments', []))
            st.write(f"💬 {comment_count}")
        
        # 댓글 섹션
        with st.expander(f"댓글 보기 ({len(post.get('comments', []))})"):
            display_comments(post, index)

def display_comments(post, post_index):
    # 기존 댓글 표시
    for i, comment in enumerate(post.get('comments', [])):
        st.markdown(f"""
        <div style="background-color: #e9ecef; padding: 8px; margin: 5px 0; border-radius: 5px;">
            <small><strong>{comment['author']}</strong> - {comment['timestamp']}</small><br>
            ⤷ {comment['content']}
        </div>
        """, unsafe_allow_html=True)
    
    # 새 댓글 작성
    with st.form(f"comment_form_{post_index}"):
        new_comment = st.text_input("댓글 작성 (최대 140자)", max_chars=140, key=f"comment_input_{post_index}")
        submit_comment = st.form_submit_button("댓글 달기")
        
        if submit_comment and new_comment:
            posts = load_posts()
            if 'comments' not in posts[post['id']]:
                posts[post['id']]['comments'] = []
            
            comment_data = {
                "content": new_comment,
                "author": st.session_state.username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            posts[post['id']]['comments'].append(comment_data)
            save_posts(posts)
            st.success("댓글이 추가되었습니다!")
            st.rerun()

# 기업 정보 수정
def edit_companies(user_data, data):
    st.markdown("### ⚙️ 기업 정보 관리")
    
    # Destiny 기업 수정
    st.markdown("#### 🎯 Destiny 기업 설정")
    
    with st.form("destiny_form"):
        destiny = user_data["destiny_company"]
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("기업명", value=destiny.get("name", ""))
            current_price = st.number_input("현재가 (원)", value=destiny.get("current_price", 0))
        with col2:
            target_buy = st.number_input("매수 목표가 (원)", value=destiny.get("target_buy", 0))
            target_sell = st.number_input("매도 목표가 (원)", value=destiny.get("target_sell", 0))
        
        description = st.text_area("기업 특징", value=destiny.get("description", ""))
        
        if st.form_submit_button("Destiny 기업 저장"):
            user_data["destiny_company"] = {
                "name": name,
                "current_price": current_price,
                "target_buy": target_buy,
                "target_sell": target_sell,
                "description": description
            }
            data[st.session_state.username] = user_data
            save_data(data)
            st.success("Destiny 기업이 저장되었습니다!")
    
    st.markdown("#### 🔍 관심 기업 5개 설정")
    
    # 관심 기업들 수정
    for i in range(5):
        with st.expander(f"관심 기업 {i+1}"):
            with st.form(f"company_form_{i}"):
                company = user_data["interesting_companies"][i]
                
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("기업명", value=company.get("name", ""), key=f"name_{i}")
                    current_price = st.number_input("현재가 (원)", value=company.get("current_price", 0), key=f"price_{i}")
                with col2:
                    target_buy = st.number_input("매수 목표가 (원)", value=company.get("target_buy", 0), key=f"buy_{i}")
                    target_sell = st.number_input("매도 목표가 (원)", value=company.get("target_sell", 0), key=f"sell_{i}")
                
                description = st.text_area("기업 특징", value=company.get("description", ""), key=f"desc_{i}")
                
                if st.form_submit_button(f"기업 {i+1} 저장"):
                    user_data["interesting_companies"][i] = {
                        "name": name,
                        "current_price": current_price,
                        "target_buy": target_buy,
                        "target_sell": target_sell,
                        "description": description
                    }
                    data[st.session_state.username] = user_data
                    save_data(data)
                    st.success(f"관심 기업 {i+1}이 저장되었습니다!")

# 메인 애플리케이션
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()