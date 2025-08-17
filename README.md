**주소** 
https://cvalueinvestment-j67mjhzqlkoapmgbxghncy.streamlit.app/

# C_value_investment 
 - Claude와 함께 만드는 가치주 일지
 
## 1) 프로젝트 개요

관심 기업의 "현재가"와 등락을 확인하고, 
나만의 "리서치 글"을 작성하고 공유하는 주식일지 커뮤니티 앱입니다. 
네이버 증권에서 **현재가·등락률**을 가져오고, 
글/댓글/리액션(좋아요·리트윗 카운트)을 **로컬 JSON 파일**로 영구 저장합니다.

“작동하는 최소 기능(MVP)”에 집중했습니다.  
버튼 한 번으로 데이터 갱신, 글쓰기·피드 통합, 간단한 반응(좋아요/리트윗)하도록 했습니다. 

## 2) 주요 기능

- 로그인/회원가입: 해시(sha256)로 4자리 비밀번호 저장 (`users_data_v2.json`)
- 관심 기업 관리: Destiny 1개 + Interesting 5개  
- 네이버 증권 크롤링: 현재가, 등락/등락률(5분 캐시)  
- 대시보드: 기업 정보(현재가/매수·매도 목표, 특징, 게시글 작성 정보)
- 리서치 게시글: 글쓰기 + 피드 + 댓글(140자), 좋아요/리트윗 카운트
- CSV 내보내기: 현재 필터링된 게시글을 CSV 다운로드

## 3) 기술 스택

- **Frontend/UI**: Streamlit
- **Backend/Storage**: Python, JSON 파일 저장
- **Crawling**: `requests` + `beautifulsoup4`
- **배포**: Streamlit Cloud

## 4) 폴더 & 데이터 구조
- `main2.py` — 앱 엔트리 포인트(배포 시 Main file)
- `users_data_v2.json` — 사용자 계정/프로필
- `investment_data_v2.json` — 관심 기업(현재가/목표가/특징/업데이트 시각)
- `posts_data_v2.json` — 리서치 게시글, 좋아요/리트윗 카운트, 댓글
- Streamlit Cloud가 `requirements.txt`를 사용해 의존성을 설치함을 확인하여 
  main2.py에 반영된 내용은 후에 추가 하여 배포준비 하였습니다.

## 5) 설치 & 실행 (로컬)
```bash
git clone <https://github.com/lion-nara/C_value_investment.git>
cd <C_value_investment>
pip install -r requirements.txt   # streamlit, requests, beautifulsoup4, lxml, pandas
streamlit run main2.py

