========================================
  이모티콘 트렌드 리포트 자동화 도구
========================================

[ 처음 시작하기 ]

1. Python 설치 (없는 경우)
   https://www.python.org/downloads/
   설치 시 "Add python.exe to PATH" 반드시 체크!

2. setup.bat 더블클릭 (첫 1회만)
   - 필요 라이브러리 자동 설치
   - 매주 월요일 09:00 자동 실행 등록

3. run.bat 더블클릭 → 즉시 리포트 생성

[ 폴더 구조 ]

emoticon-report/
├── main.py              ← 메인 실행 파일
├── run.bat              ← 더블클릭으로 즉시 실행
├── setup.bat            ← 최초 1회 설치
├── README.txt           ← 이 파일
├── src/
│   ├── kakao_scraper.py      ← 카카오 이모티콘 수집
│   ├── instagram_scraper.py  ← 인스타/구글 트렌드 수집
│   └── report_generator.py   ← HTML 리포트 생성
└── reports/             ← 생성된 리포트 저장 위치
    └── emoticon_trend_YYYYMMDD_HHMM.html

[ 수집 데이터 ]

■ 카카오 이모티콘샵
  - 인기 순위 Top 30
  - 썸네일, 작가, 가격 정보

■ 인스타그램 해시태그
  - #이모티콘 #카카오이모티콘 #카카오프렌즈 등
  - 각 해시태그 게시물 수 추이

■ Google Trends KR
  - 이모티콘/캐릭터 관련 급상승 검색어

[ 스케줄 변경 방법 ]

작업 스케줄러 열기 → Win+R → taskschd.msc
→ 작업 스케줄러 라이브러리 → EmoticonTrendReport

[ 문의 ]

카카오 이모티콘샵 정책 변경으로 수집이 안 될 경우,
카카오 API 공식 문서를 참고하세요:
https://developers.kakao.com/
