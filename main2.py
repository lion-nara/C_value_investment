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
    
    .current-price {
        font-size: 1.2em;
        font-weight: bold;
        color: #28a745;
    }
    
    .price-change-up {
        color: #dc3545;
        font-weight: bold;
    }
    
    .price-change-down {
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
    
    .auth-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 10px;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# 데이터 파일 경로 (v2용으로 분리)
DATA_FILE = "investment_data_v2.json"
POSTS_FILE = "posts_data_v2.json"
USERS_FILE = "users_data_v2.json"

# 네이버 증권 주가 크롤링 함수
@st.cache_data(ttl=300)  # 5분 캐시
def get_stock_price(stock_code):
    """네이버 증권에서 주가 정보를 가져옵니다."""
    try:
        url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 현재가 찾기 - 여러 방법 시도
        current_price = None
        
        # 방법 1: no_today 클래스의 blind 요소
        price_element = soup.select_one('.no_today .blind')
        if price_element:
            price_text = price_element.text.strip()
            # 숫자와 콤마만 추출
            price_numbers = ''.join(c for c in price_text if c.isdigit() or c == ',')
            if price_numbers:
                current_price = int(price_numbers.replace(',', ''))
        
        # 방법 2: 첫 번째 blind 요소 (방법 1이 실패한 경우)
        if current_price is None:
            blind_elements = soup.select('.blind')
            for element in blind_elements:
                text = element.text.strip()
                # 숫자로만 구성된 텍스트 찾기 (콤마 포함)
                numbers_only = ''.join(c for c in text if c.isdigit() or c == ',')
                if numbers_only and len(numbers_only) >= 3:  # 최소 3자리 이상
                    try:
                        current_price = int(numbers_only.replace(',', ''))
                        break
                    except:
                        continue
        
        if current_price is None:
            return None
            
        # 전일대비 정보 찾기
        change = 0
        change_rate = 0.0
        
        # 전일대비 금액과 퍼센트 찾기
        blind_elements = soup.select('.blind')
        for i, element in enumerate(blind_elements):
            text = element.text.strip()
            
            # 변동 금액 찾기 (두 번째나 세 번째 요소)
            if i > 0 and i < len(blind_elements) - 1:
                # 숫자만 추출해서 변동 금액인지 확인
                numbers_only = ''.join(c for c in text if c.isdigit() or c == ',')
                if numbers_only and len(numbers_only) <= 6:  # 변동금액은 보통 현재가보다 작음
                    try:
                        change_value = int(numbers_only.replace(',', ''))
                        if change_value > 0 and change_value < current_price:
                            change = change_value
                            # 상승/하락 판단
                            parent_text = str(element.parent) if element.parent else ""
                            if 'minus' in parent_text or 'down' in parent_text.lower():
                                change = -change
                            break
                    except:
                        continue
        
        # 변동률 찾기
        for element in blind_elements:
            text = element.text.strip()
            if '%' in text:
                try:
                    # 퍼센트 기호와 +,- 기호 제거 후 숫자만 추출
                    rate_text = text.replace('%', '').replace('+', '').replace('-', '').strip()
                    change_rate = float(rate_text)
                    # 변동 금액이 음수면 변동률도 음수로
                    if change < 0:
                        change_rate = -abs(change_rate)
                    else:
                        change_rate = abs(change_rate)
                    break
                except:
                    continue
        
        return {
            'price': current_price,
            'change': change,
            'change_rate': change_rate,
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except requests.exceptions.RequestException as e:
        st.error(f"네트워크 오류: 인터넷 연결을 확인해주세요.")
        return None
    except Exception as e:
        st.error(f"주가 정보를 가져올 수 없습니다. 주식 코드를 확인해주세요. (코드: {stock_code})")
        return None

# 비밀번호 해시화
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    return hash_password(password) == hashed_password

# 사용자 데이터 관리
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

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
            "stock_code": "",
            "current_price": 0,
            "target_buy": 0,
            "target_sell": 0,
            "description": "",
            "last_updated": ""
        },
        "interesting_companies": [
            {
                "name": "",
                "stock_code": "",
                "current_price": 0,
                "target_buy": 0,
                "target_sell": 0,
                "description": "",
                "last_updated": ""
            } for _ in range(5)
        ]
    }

# 세션 상태 초기화
if 'logged_in_v2' not in st.session_state:
    st.session_state.logged_in_v2 = False
if 'username_v2' not in st.session_state:
    st.session_state.username_v2 = ""

# 로그인/회원가입 화면
def auth_page():
    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
    
    st.title("📈 가치주 분석 커뮤니티 v2")
    st.caption("🚀 실시간 주가 연동 + 강화된 보안")
    
    tab1, tab2 = st.tabs(["🔑 로그인", "👤 회원가입"])
    
    with tab1:
        login_form()
    
    with tab2:
        signup_form()
    
    st.markdown("</div>", unsafe_allow_html=True)

def login_form():
    st.markdown("### 로그인")
    
    users = load_users()
    
    with st.form("login_form_v2"):
        username = st.text_input("사용자명", placeholder="사용자명을 입력하세요")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        login_button = st.form_submit_button("로그인", use_container_width=True)
        
        if login_button:
            if username in users:
                if verify_password(password, users[username]['password']):
                    st.session_state.logged_in_v2 = True
                    st.session_state.username_v2 = username
                    st.success("로그인 성공!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("비밀번호가 올바르지 않습니다.")
            else:
                st.error("존재하지 않는 사용자명입니다.")

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
            if not username:
                st.error("사용자명을 입력해주세요.")
            elif not password:
                st.error("비밀번호를 입력해주세요.")
            elif password != password_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            elif username in users:
                st.error("이미 존재하는 사용자명입니다.")
            elif len(password) < 4:
                st.error("비밀번호는 최소 4자 이상이어야 합니다.")
            else:
                # 새 사용자 등록
                users[username] = {
                    'password': hash_password(password),
                    'email': email,
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                save_users(users)
                st.success("회원가입 완료! 로그인 탭에서 로그인해주세요.")

# 메인 대시보드
def main_dashboard():
    data = load_data()
    
    if st.session_state.username_v2 not in data:
        data[st.session_state.username_v2] = initialize_user_data(st.session_state.username_v2)
        save_data(data)
    
    user_data = data[st.session_state.username_v2]
    
    # 헤더
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.title(f"📈 {st.session_state.username_v2}님의 투자 대시보드 v2")
    with col2:
        if st.button("🔄 주가 업데이트"):
            update_stock_prices(user_data, data)
            st.success("주가 업데이트 완료!")
            st.rerun()
    with col3:
        if st.button("로그아웃"):
            st.session_state.logged_in_v2 = False
            st.session_state.username_v2 = ""
            st.rerun()
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📊 내 관심 기업", "📝 리서치 게시글", "⚙️ 기업 정보 수정"])
    
    with tab1:
        display_companies(user_data)
    
    with tab2:
        research_posts()
    
    with tab3:
        edit_companies(user_data, data)

# 주가 업데이트 함수
def update_stock_prices(user_data, data):
    """모든 등록된 주식의 가격을 업데이트합니다."""
    
    # Destiny 기업 업데이트
    if user_data["destiny_company"]["stock_code"]:
        stock_info = get_stock_price(user_data["destiny_company"]["stock_code"])
        if stock_info:
            user_data["destiny_company"]["current_price"] = stock_info['price']
            user_data["destiny_company"]["last_updated"] = stock_info['updated_at']
            user_data["destiny_company"]["change"] = stock_info['change']
            user_data["destiny_company"]["change_rate"] = stock_info['change_rate']
    
    # 관심 기업들 업데이트
    for company in user_data["interesting_companies"]:
        if company["stock_code"]:
            stock_info = get_stock_price(company["stock_code"])
            if stock_info:
                company["current_price"] = stock_info['price']
                company["last_updated"] = stock_info['updated_at']
                company["change"] = stock_info['change']
                company["change_rate"] = stock_info['change_rate']
    
    data[st.session_state.username_v2] = user_data
    save_data(data)

            
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
        # 투자 신호 계산
        investment_signal = ""
        signal_color = "#333"
        
        if company.get('current_price', 0) > 0:
            if company['current_price'] <= company.get('target_buy', 0):
                investment_signal = "🟢 매수 신호"
                signal_color = "#28a745"
            elif company['current_price'] >= company.get('target_sell', 0):
                investment_signal = "🔴 매도 신호"  
                signal_color = "#dc3545"
            else:
                investment_signal = "🟡 관망"
                signal_color = "#ffc107"
        
        # 등락 정보
        change_info = ""
        if company.get('change') is not None and company.get('change_rate') is not None:
            change = company['change']
            change_rate = company['change_rate']
            if change > 0:
                change_info = f'<span class="price-change-up">▲{change:,}원 (+{change_rate:.2f}%)</span>'
            elif change < 0:
                change_info = f'<span class="price-change-down">▼{abs(change):,}원 ({change_rate:.2f}%)</span>'
            else:
                change_info = f'<span>보합 (0.00%)</span>'
        
        last_updated = company.get('last_updated', '')
        if last_updated:
            last_updated_text = f"<small>📅 업데이트: {last_updated}</small>"
        else:
            last_updated_text = ""
        
        st.markdown(f"""
        <div class="company-card">
            <h4>🏢 {company['name']} ({company.get('stock_code', 'N/A')})</h4>
            <p class="current-price">현재가: {company['current_price']:,}원 {change_info}</p>
            <p>
                <span class="valuation-buy">매수 목표: {company['target_buy']:,}원</span> | 
                <span class="valuation-sell">매도 목표: {company['target_sell']:,}원</span>
            </p>
            <p><strong style="color: {signal_color};">{investment_signal}</strong></p>
            <p><strong>특징:</strong> {company['description']}</p>
            {last_updated_text}
        </div>
        """, unsafe_allow_html=True)
        
        # 리서치 작성 버튼
        button_key = f"research_v2_{'destiny' if is_destiny else f'company_{company_index}'}_{company['name']}"
        if st.button(f"📝 {company['name']} 리서치 작성", key=button_key):
            st.session_state.selected_company_v2 = company['name']
            st.session_state.show_research_form_v2 = True

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
            key="company_filter_v2"
        )
  

    # 새 리서치 작성
    if st.session_state.get('show_research_form_v2', False):
        write_research_post(posts)
    
    if not st.session_state.get('show_research_form_v2', False):
        if st.button("✍️ 새 리서치 작성"):
            st.session_state.show_research_form_v2 = True
            st.rerun()
    
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
    
    with st.form("research_form_v2"):
        company = st.text_input("기업명", value=st.session_state.get('selected_company_v2', ''))
        content = st.text_area("리서치 내용", height=150, max_chars=500)
        is_public = st.checkbox("공개 설정", value=True)
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("게시하기", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("취소", use_container_width=True)
        
        if cancel:
            st.session_state.show_research_form_v2 = False
            if 'selected_company_v2' in st.session_state:
                del st.session_state.selected_company_v2
            st.rerun()
        
        if submit and company and content:
            new_post = {
                "id": len(posts),
                "company": company,
                "content": content,
                "author": st.session_state.username_v2,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_public": is_public,
                "likes": 0,
                "retweets": 0,
                "comments": []
            }
            posts.append(new_post)
            save_posts(posts)
            st.session_state.show_research_form_v2 = False
            if 'selected_company_v2' in st.session_state:
                del st.session_state.selected_company_v2
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
            if st.button(f"❤️ {post['likes']}", key=f"like_v2_{index}"):
                posts = load_posts()
                posts[post['id']]['likes'] += 1
                save_posts(posts)
                st.rerun()
        
        with col2:
            if st.button(f"🔄 {post['retweets']}", key=f"retweet_v2_{index}"):
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
    with st.form(f"comment_form_v2_{post_index}"):
        new_comment = st.text_input("댓글 작성 (최대 140자)", max_chars=140, key=f"comment_input_v2_{post_index}")
        submit_comment = st.form_submit_button("댓글 달기")
        
        if submit_comment and new_comment:
            posts = load_posts()
            if 'comments' not in posts[post['id']]:
                posts[post['id']]['comments'] = []
            
            comment_data = {
                "content": new_comment,
                "author": st.session_state.username_v2,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            posts[post['id']]['comments'].append(comment_data)
            save_posts(posts)
            st.success("댓글이 추가되었습니다!")
            st.rerun()

# 기업 정보 수정
def edit_companies(user_data, data):
    st.markdown("### ⚙️ 기업 정보 관리")
    
    st.info("💡 **주식 코드 찾는 방법:** 네이버 증권에서 기업 검색 후 URL의 code= 뒤 6자리 숫자를 입력하세요. (예: 삼성전자 = 005930)")
    
    # Destiny 기업 수정
    st.markdown("#### 🎯 Destiny 기업 설정")
    
    with st.form("destiny_form_v2"):
        destiny = user_data["destiny_company"]
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("기업명", value=destiny.get("name", ""))
            stock_code = st.text_input("주식 코드 (6자리)", value=destiny.get("stock_code", ""), max_chars=6)
            current_price = st.number_input("현재가 (원)", value=destiny.get("current_price", 0))
        with col2:
            target_buy = st.number_input("매수 목표가 (원)", value=destiny.get("target_buy", 0))
            target_sell = st.number_input("매도 목표가 (원)", value=destiny.get("target_sell", 0))
        
        description = st.text_area("기업 특징", value=destiny.get("description", ""))
        
        col1, col2 = st.columns(2)
        with col1:
            save_button = st.form_submit_button("💾 Destiny 기업 저장", use_container_width=True)
        with col2:
            if stock_code and len(stock_code) == 6:
                test_price = st.form_submit_button("🔍 주가 확인", use_container_width=True)
                if test_price:
                    with st.spinner("주가 정보를 가져오는 중..."):
                        stock_info = get_stock_price(stock_code)
                        if stock_info:
                            st.success(f"현재가: {stock_info['price']:,}원")
                        else:
                            st.error("주가 정보를 가져올 수 없습니다. 주식 코드를 확인해주세요.")
        
        if save_button:
            user_data["destiny_company"] = {
                "name": name,
                "stock_code": stock_code,
                "current_price": current_price,
                "target_buy": target_buy,
                "target_sell": target_sell,
                "description": description,
                "last_updated": destiny.get("last_updated", "")
            }
            data[st.session_state.username_v2] = user_data
            save_data(data)
            st.success("Destiny 기업이 저장되었습니다!")
    
    st.markdown("#### 🔍 관심 기업 5개 설정")
    
    # 관심 기업들 수정
    for i in range(5):
        with st.expander(f"관심 기업 {i+1}"):
            with st.form(f"company_form_v2_{i}"):
                company = user_data["interesting_companies"][i]
                
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("기업명", value=company.get("name", ""), key=f"name_v2_{i}")
                    stock_code = st.text_input("주식 코드 (6자리)", value=company.get("stock_code", ""), max_chars=6, key=f"code_v2_{i}")
                    current_price = st.number_input("현재가 (원)", value=company.get("current_price", 0), key=f"price_v2_{i}")
                with col2:
                    target_buy = st.number_input("매수 목표가 (원)", value=company.get("target_buy", 0), key=f"buy_v2_{i}")
                    target_sell = st.number_input("매도 목표가 (원)", value=company.get("target_sell", 0), key=f"sell_v2_{i}")
                
                description = st.text_area("기업 특징", value=company.get("description", ""), key=f"desc_v2_{i}")
                
                col1, col2 = st.columns(2)
                with col1:
                    save_button = st.form_submit_button(f"💾 기업 {i+1} 저장", use_container_width=True)
                with col2:
                    if stock_code and len(stock_code) == 6:
                        test_price = st.form_submit_button(f"🔍 주가 확인", use_container_width=True, key=f"test_v2_{i}")
                        if test_price:
                            with st.spinner("주가 정보를 가져오는 중..."):
                                stock_info = get_stock_price(stock_code)
                                if stock_info:
                                    st.success(f"현재가: {stock_info['price']:,}원")
                                else:
                                    st.error("주가 정보를 가져올 수 없습니다. 주식 코드를 확인해주세요.")
                
                if save_button:
                    user_data["interesting_companies"][i] = {
                        "name": name,
                        "stock_code": stock_code,
                        "current_price": current_price,
                        "target_buy": target_buy,
                        "target_sell": target_sell,
                        "description": description,
                        "last_updated": company.get("last_updated", "")
                    }
                    data[st.session_state.username_v2] = user_data
                    save_data(data)
                    st.success(f"관심 기업 {i+1}이 저장되었습니다!")

                   
# 메인 애플리케이션
def main():
    if not st.session_state.logged_in_v2:
        auth_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()