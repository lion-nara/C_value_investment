**주소** 
https://cvalueinvestment-j67mjhzqlkoapmgbxghncy.streamlit.app/


# C_value_investment 
 - Claude와 함께 만드는 가치투자를 위한 기업 일지 커뮤니티


## 1) 프로젝트 개요

- 관심 기업의 "현재가"와 등락을 확인하고, 나만의 "리서치 글"을 작성하고 공유하는 주식일지 커뮤니티 앱입니다. 
- 네이버 증권에서 **현재가·등락률**을 가져와서 매도, 매수 현황을 알려줍니다.
- 글/댓글/리액션(좋아요·리트윗 카운트)을 **로컬 JSON 파일**로 영구 저장합니다.
- 버튼 한 번으로 일지작성 날짜와 리서치 분야를 선택하는 최소 기능에 집중했습니다.  
- 데이터 갱신, 글쓰기·피드 통합, 간단한 반응(좋아요/리트윗)하도록 했습니다. 

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
- Streamlit Cloud가 `requirements.txt`를 사용해 의존성을 설치함을 확인하여 main2.py에 반영된 내용은 후에 추가 하여 배포준비 하였습니다.

## 5) 설치 & 실행 (로컬)

- git clone <https://github.com/lion-nara/C_value_investment.git>
- cd <C_value_investment>
- pip install -r requirements.txt   # streamlit, requests, beautifulsoup4, lxml, pandas
- streamlit run main2.py

## 6)  사용방법

- 회원가입/로그인
- 상단 탭에서 ⚙️ 기업 정보 수정 → Destiny & Interesting 입력/저장
- 내 관심 기업 탭에서 카드 확인 → (선택) 주가 업데이트
- 리서치 게시글 탭에서 글 작성 → 빠른삽입 버튼/날짜 삽입 활용
- 피드에서 좋아요/리트윗 카운트, 댓글(140자)
- (필요 시) CSV 다운로드로 제출용 자료 저장

## 7) 네이버 크롤링 작동 원리 (with Claude)

- requests로 네이버 증권 HTML을 가져오고
- beautifulsoup4로 HTML을 파싱해서 현재가/등락 텍스트만 뽑습니다.
- @st.cache_data(ttl=300)로 5분 캐시하여 불필요한 반복 요청을 줄입니다.

## 8) 한계 & 개선 계획

- 네이버 페이지 구조가 바뀌면 크롤링이 실패할 수 있음을 확인하였습니다 → 예외 처리 보강 예정
- 리트윗은 “숫자 토글”만 제공 (중복 포스트 생성 X)
- 추후: 종목 검색 자동완성, 사용자별 통계, 모바일 최적화, DB(SQLite) 전환

## 9) 커밋 히스토리

- 첫 프로젝트 - 가치주 크롤드 버전 
    : 원하는 작업 내용과 창 이동을 워드로 대략 작성하고 Claude, Chat-GPT와 함께 기본틀(main.py)을 정리
- main2 가치주 : 기본 작업(main)에서 현재가를 반영한 코드로 변경
- 가치주 v2 bs4 보완 
    : 최종 클라우드를 위해 requirements2가 아닌 requirement.txt에 누락 패키지(beautifulsoup4) 추가
- README.md 정보수정 : 업데이트 및 배포 링크

