# 네이버 날씨 홈 위젯 플러그인 (v2.0.0)

## v2.0.0 — 진짜 CSS/이미지로 렌더링 (대규모 개편)

코어에 `dashboard.html`/`dashboard.css`/`dashboard.js`(Shadow DOM 격리 렌더링, **코어 버전
1.1.1+ 필요**) 계약이 추가되면서, 더 이상 "라벨: 값" 텍스트 카드 제약 없이 완전한 CSS와
SVG 아이콘으로 위젯을 그릴 수 있게 되었습니다. 이 버전부터 위젯은 스크린샷과 동일하게:

- 날씨 상태 + 주/야간에 맞는 SVG 아이콘(해/달/구름/비/눈/번개)
- 큰 숫자의 현재 기온
- 어제 대비, 최저/최고
- 체감·바람·습도·미세먼지·초미세먼지·일출·일몰을 하단 통계 그리드로 표시

를 실제 카드 디자인으로 보여줍니다.

**코어가 1.1.1 미만이면** `dashboard.html` 등은 무시되고 이전처럼 텍스트 카드로 표시됩니다
(하위 호환) — 다만 이 경우 진짜 CSS 디자인 대신 "라벨: 값" 텍스트만 나오니, 코어를 최신
버전으로 업데이트하는 것을 권장합니다.

## 설치
1. 이 `naver_weather` 폴더 전체를 BookOasis 서버의 `plugins/metadata/` 아래에 복사합니다.
   ```
   plugins/metadata/
     naver_weather/
       __init__.py
       naver_weather.py
       VERSION
       requirements.txt
       dashboard.html   # 위젯 마크업 (v2.0.0 신규)
       dashboard.css    # 위젯 전용 스타일 (v2.0.0 신규)
       dashboard.js     # 위젯 렌더링 로직 (v2.0.0 신규)
   ```
2. 서버를 재시작합니다. (`requirements.txt`의 `requests`가 자동으로 플러그인 전용 `libs/`에 설치됩니다.)
3. 환경설정 > 플러그인 설정에서 "네이버 날씨 위젯"을 활성화합니다.
4. 아래 "지역 설정" 안내에 따라 **REGION_CODE**를 입력하고 저장합니다 (강력 권장).

## 지역 설정 (중요)

`weather.naver.com/today`는 검색 쿼리 텍스트가 아니라 **접속 세션/IP 기준으로 이미 정해진
지역**의 날씨를 보여주는 구조입니다. 그래서 지역명만으로는 원하는 지역이 정확히 나온다는
보장이 없습니다.

**해결책: REGION_CODE(지역 고유 코드)를 직접 찾아서 입력하세요.**

1. 브라우저로 https://weather.naver.com 에 접속합니다.
2. 우측 상단 검색(돋보기)으로 원하는 지역(예: "광주광역시 광산구")을 검색해 선택합니다.
3. 주소창의 URL이 `https://weather.naver.com/today/18330600` 같은 형태로 바뀝니다 —
   마지막의 숫자(`18330600`)가 REGION_CODE입니다.
4. 이 숫자를 플러그인 설정의 **REGION_CODE** 항목에 그대로 입력하고 저장합니다.

REGION_CODE를 입력하지 않으면 네이버의 비공식 지역 자동완성 API로 변환을 시도하지만, 문서화
되지 않은 API라 언제든 실패할 수 있습니다(이 경우 위젯에 안내 문구가 표시됩니다).

## 표시 방식(DISPLAY_MODE)

환경설정 > 플러그인 설정에서 두 가지 중 고를 수 있습니다:

- **SMALL** (기본값) — 스크린샷과 동일한 풀 비주얼 카드. 아이콘 + 큰 온도 숫자 + 하단
  통계 그리드로 표시됩니다.
- **GENERAL** — 항목별로 한 줄씩 나열하는 리스트 형태. 아래 SHOW_* 체크박스로 각 행을
  켜고 끌 수 있습니다.

두 모드 모두 아래 SHOW_* 설정을 공유합니다 — 예를 들어 `SHOW_WIND`를 꺼두면 SMALL
모드의 바람 칸도, GENERAL 모드의 바람 행도 함께 사라집니다.

- `SHOW_RANGE` — 최저/최고 기온
- `SHOW_FEELS_LIKE` — 체감온도
- `SHOW_WIND` — 바람(풍향/풍속)
- `SHOW_HUMIDITY` — 습도
- `SHOW_PM10` — 미세먼지
- `SHOW_PM25` — 초미세먼지
- `SHOW_SUNRISE` — 일출
- `SHOW_SUNSET` — 일몰

### CACHE_TTL_SECONDS
기본 600초(10분) 동안은 같은 결과를 재사용해 네이버에 과도하게 요청하지 않습니다.

## 홈 화면에 노출하기
`home_widget` 계약을 사용했기 때문에, **사용자가 "내 설정 > 홈 화면 플러그인 배치 모드"를 켜야**
홈 화면 하단의 "+ 위젯 추가" 목록에 이 위젯이 나타납니다. 목록에서 선택해야 실제 홈 화면에
카드로 추가됩니다(설치만으로는 자동 노출되지 않음).

## 동작 방식

- `weather.naver.com/today/{REGION_CODE}` 페이지를 서버에서 가져와, 페이지에 인라인으로
  삽입된 `var blockApiResult = {...};` JSON을 직접 파싱합니다 (`nowSynthesisFcast` 블록의
  `nowFcast`/`airFcast`/`weeklyFcastList`/`sunRiseSetList`).
- `get_dashboard_data()`는 더 이상 텍스트 카드(`item_type: metric`) 목록이 아니라, 파싱한
  원시 데이터 필드를 그대로 담은 payload 딕셔너리 1개를 반환합니다. 실제 화면은
  `dashboard.js`가 이 payload를 읽어 Shadow DOM 안에 그립니다.
- 주/야간 아이콘 판정은 일출/일몰 시각과 서버의 현재 시각을 문자열 비교(`HH:MM`)해서
  결정합니다 — 별도 시간대 라이브러리 없이도 충분히 정확합니다.
- **네이버가 이 JSON 구조나 변수명을 바꾸면 파싱이 깨질 수 있습니다.** 이 경우 위젯은
  에러 대신 "정보를 불러오지 못했습니다" 안내만 표시하도록(fail-soft) 만들어져 있습니다.
  계속 안내만 뜬다면 `naver_weather.py`의 `_extract_block_api_result()` / `_parse_weather()`를
  최신 페이지 구조에 맞게, 또는 `dashboard.html`/`dashboard.js`를 최신 디자인에 맞게
  업데이트해야 합니다.
- 외부 사이트 스크래핑이라는 특성상 네이버 이용약관/요청 빈도 정책을 참고해 캐시 TTL을
  너무 짧게 두지 않는 것을 권장합니다(기본값 10분).
