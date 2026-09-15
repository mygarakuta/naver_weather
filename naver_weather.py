# -*- coding: utf-8 -*-
"""
BookOasis 홈 화면용 네이버 날씨 위젯 플러그인 (v1.4.0)

v1.4.0 변경 사항:
- 날씨상태·현재기온·최저/최고·습도를 별도 카드로 나누지 않고 메인 카드 하나(설명란)에
  모두 묶어서 표시하도록 변경했습니다. SHOW_RANGE/SHOW_HUMIDITY 설정은 이제 "별도 카드
  표시 여부"가 아니라 "메인 카드 설명란에 포함할지"를 제어합니다.

v1.3.0 변경 사항:
- 최저/최고, 체감, 바람, 습도, 미세먼지, 초미세먼지, 일출, 일몰 각 카드를
  플러그인 설정 화면에서 체크박스로 개별 표시/숨김 할 수 있도록 config_schema를
  추가했습니다 (위치+현재기온 메인 카드는 항상 표시됩니다).

v1.1.0 변경 사항:
- weather.naver.com/today 페이지가 HTML class 기반이 아니라 `var blockApiResult = {...}`
  라는 인라인 JSON 변수에 모든 실데이터(현재기온/날씨상태/미세먼지)를 담아 내려주는 구조임을
  반영해 파싱 로직을 JSON 파싱 방식으로 전면 교체했습니다.
- weather.naver.com/today 는 검색 쿼리와 무관하게 세션/IP 기준 지역을 보여줄 수 있으므로,
  이름 검색(자동완성 API, best-effort)보다 REGION_CODE(지역 고유 코드) 직접 입력을 우선
  사용하도록 변경했습니다.
"""

import json
import re

import requests

from plugins.metadata.base import BaseMetadataProvider


class NaverWeatherProvider(BaseMetadataProvider):
    # 네임스페이스 접두사는 자유롭게 본인 것으로 바꿔서 사용하세요 (예: yourname.naver_weather)
    id = "naver_weather"
    name = "네이버 날씨 위젯"
    is_searchable = False

    config_schema = [
        {
            "key": "REGION_CODE",
            "label": "네이버 날씨 지역 코드 (강력 권장 - 찾는 법은 README 참고)",
            "type": "text",
            "required": False,
        },
        {
            "key": "LOCATION",
            "label": "지역명 (REGION_CODE 미입력 시 자동 검색 시도 - 부정확할 수 있음)",
            "type": "text",
            "default": "서울",
        },
        {
            "key": "CACHE_TTL_SECONDS",
            "label": "캐시 유지 시간(초)",
            "type": "number",
            "default": 600,
        },
        {
            "key": "SHOW_RANGE",
            "label": "메인 카드에 최저/최고 기온 포함",
            "type": "checkbox",
            "default": True,
        },
        {
            "key": "SHOW_FEELS_LIKE",
            "label": "체감온도 카드 표시",
            "type": "checkbox",
            "default": True,
        },
        {
            "key": "SHOW_WIND",
            "label": "바람(풍향/풍속) 카드 표시",
            "type": "checkbox",
            "default": True,
        },
        {
            "key": "SHOW_HUMIDITY",
            "label": "메인 카드에 습도 포함",
            "type": "checkbox",
            "default": True,
        },
        {
            "key": "SHOW_PM10",
            "label": "미세먼지 카드 표시",
            "type": "checkbox",
            "default": True,
        },
        {
            "key": "SHOW_PM25",
            "label": "초미세먼지 카드 표시",
            "type": "checkbox",
            "default": True,
        },
        {
            "key": "SHOW_SUNRISE",
            "label": "일출 카드 표시",
            "type": "checkbox",
            "default": True,
        },
        {
            "key": "SHOW_SUNSET",
            "label": "일몰 카드 표시",
            "type": "checkbox",
            "default": True,
        },
    ]

    update_manifest = {"enabled": False}

    home_widget = {
        "title": "오늘의 날씨",
        "subtitle": "네이버 날씨",
        "icon": "fa-solid fa-cloud-sun",
        "order": 15,
        "limit": 10,
        "sessions": "all",
        "layout": "grid",
        "size": 1,
    }

    def search(self, db_type, query):
        return {"success": True, "items": []}

    def apply(self, db_type, book_id, item_data):
        return False, "날씨 위젯 플러그인은 메타데이터 적용을 지원하지 않습니다."

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
    }

    # --- 설정 ---

    @staticmethod
    def _as_bool(value, default=True):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() not in ("false", "0", "", "no", "off")
        return bool(value)

    def _get_config(self, db_type):
        cfg = self.get_plugin_config(db_type, default={})
        region_code = str(cfg.get("REGION_CODE") or "").strip()
        location = str(cfg.get("LOCATION") or "서울").strip()
        try:
            ttl = int(cfg.get("CACHE_TTL_SECONDS") or 600)
        except (TypeError, ValueError):
            ttl = 600

        visibility = {
            "range": self._as_bool(cfg.get("SHOW_RANGE")),
            "feels_like": self._as_bool(cfg.get("SHOW_FEELS_LIKE")),
            "wind": self._as_bool(cfg.get("SHOW_WIND")),
            "humidity": self._as_bool(cfg.get("SHOW_HUMIDITY")),
            "pm10": self._as_bool(cfg.get("SHOW_PM10")),
            "pm25": self._as_bool(cfg.get("SHOW_PM25")),
            "sunrise": self._as_bool(cfg.get("SHOW_SUNRISE")),
            "sunset": self._as_bool(cfg.get("SHOW_SUNSET")),
        }

        return region_code, location, max(ttl, 60), visibility

    # --- 지역명 -> 지역코드 변환 (best-effort, 실패해도 안전하게 None) ---

    def _resolve_region_code(self, location):
        """
        REGION_CODE가 비어 있을 때만 시도하는 best-effort 자동완성 조회입니다.
        네이버 비공식 API이므로 응답 형식이 언제든 바뀔 수 있고, 그 경우 이 함수는
        예외를 던지지 않고 조용히 None을 반환합니다 - 정확한 지역을 원한다면
        REGION_CODE를 직접 설정하는 것을 강력히 권장합니다.
        """
        url = "https://ac.weather.naver.com/ac"
        params = {
            "q": location,
            "r_format": "json",
            "r_enc": "UTF-8",
            "r_unicode": "0",
            "q_enc": "UTF-8",
            "st": "1",
        }
        try:
            res = requests.get(url, params=params, headers=self.HEADERS, timeout=6)
            res.raise_for_status()
            data = res.json()
        except (requests.RequestException, ValueError):
            return None

        try:
            for group in data.get("items") or []:
                for entry in group:
                    if entry and isinstance(entry, (list, tuple)) and entry[0]:
                        code = str(entry[0]).strip()
                        if code.isdigit():
                            return code
        except (TypeError, IndexError, AttributeError):
            return None
        return None

    # --- 페이지 fetch & JSON 추출 ---

    def _fetch_weather_page(self, region_code):
        url = f"https://weather.naver.com/today/{region_code}"
        try:
            res = requests.get(url, headers=self.HEADERS, timeout=8)
            res.raise_for_status()
            return res.text
        except requests.RequestException:
            return None

    def _extract_block_api_result(self, html):
        """
        페이지에 인라인으로 삽입된 `var blockApiResult = {...};` JSON을 추출합니다.
        네이버 날씨 페이지는 서버 렌더링 시점에 현재 날씨/미세먼지/주간예보 등 모든
        실데이터를 이 변수 하나에 JSON으로 심어두므로, 화면 class 기반 스크래핑보다
        이 방식이 훨씬 안정적입니다. 다음 변수 선언(`var blockData`) 직전까지를
        경계로 잘라내 파싱합니다.
        """
        m = re.search(r"var blockApiResult = (\{.*?\});\s*var blockData", html, re.DOTALL)
        if not m:
            return None
        try:
            return json.loads(m.group(1))
        except (ValueError, TypeError):
            return None

    # 풍향 코드(N/NE/E/...) -> 한글 표기
    _WIND_DIRECTION_KO = {
        "N": "북풍", "NNE": "북북동풍", "NE": "북동풍", "ENE": "동북동풍",
        "E": "동풍", "ESE": "동남동풍", "SE": "남동풍", "SSE": "남남동풍",
        "S": "남풍", "SSW": "남남서풍", "SW": "남서풍", "WSW": "서남서풍",
        "W": "서풍", "WNW": "서북서풍", "NW": "북서풍", "NNW": "북북서풍",
    }

    @staticmethod
    def _fmt_time(raw):
        """'061400' (HHMMSS) -> '06:14' 형태로 변환. 실패 시 None."""
        if not raw or not isinstance(raw, str) or len(raw) < 4:
            return None
        return f"{raw[0:2]}:{raw[2:4]}"

    @staticmethod
    def _fmt_temp(value, decimals=1):
        if value is None:
            return None
        try:
            return f"{float(value):.{decimals}f}°"
        except (TypeError, ValueError):
            return None

    def _parse_weather(self, block_api_result, location_label):
        try:
            choice_result = block_api_result["results"]["choiceResult"]
        except (KeyError, TypeError):
            return None

        # 키 이름이 "nowSynthesisFcast~~1" 처럼 동적 접미사가 붙으므로 접두사로 찾습니다.
        now_block = None
        for key, value in choice_result.items():
            if key.startswith("nowSynthesisFcast") and isinstance(value, dict):
                now_block = value
                break
        if not now_block:
            return None

        now_fcast = now_block.get("nowFcast") or {}
        air_fcast = now_block.get("airFcast") or {}
        weekly_list = now_block.get("weeklyFcastList") or []
        sun_list = now_block.get("sunRiseSetList") or []

        temperature = now_fcast.get("tmpr")
        condition = now_fcast.get("wetrTxt")

        if temperature is None and not condition:
            return None

        # 오늘 날짜(aplYmd)와 일치하는 주간예보 항목에서 최저/최고 기온을 찾습니다.
        today_ymd = now_fcast.get("aplYmd")
        min_temp = max_temp = None
        for day in weekly_list:
            if not today_ymd or day.get("aplYmd") == today_ymd:
                min_temp = self._fmt_temp(day.get("minTmpr"), 0)
                max_temp = self._fmt_temp(day.get("maxTmpr"), 0)
                break

        # 오늘 날짜와 일치하는 일출일몰 항목을 찾습니다 (없으면 첫 항목 사용).
        sun_today = None
        for entry in sun_list:
            if not today_ymd or entry.get("aplYmd") == today_ymd:
                sun_today = entry
                break
        if sun_today is None and sun_list:
            sun_today = sun_list[0]

        wind_code = now_fcast.get("windDrctn")
        wind_speed = now_fcast.get("windSpd")
        wind_label = None
        if wind_code or wind_speed is not None:
            direction_ko = self._WIND_DIRECTION_KO.get(wind_code, wind_code or "")
            speed_txt = f"{wind_speed}m/s" if wind_speed is not None else ""
            wind_label = " ".join(p for p in (direction_ko, speed_txt) if p) or None

        yesterday_diff = now_fcast.get("ytmpr")
        diff_label = None
        if yesterday_diff is not None:
            try:
                diff_val = float(yesterday_diff)
                arrow = "↑" if diff_val > 0 else ("↓" if diff_val < 0 else "-")
                diff_label = f"어제보다 {abs(diff_val):.1f}°{arrow}"
            except (TypeError, ValueError):
                diff_label = None

        humidity = now_fcast.get("humd")
        humidity_label = f"{humidity:.0f}%" if isinstance(humidity, (int, float)) else None

        return {
            "location": location_label,
            "temperature": self._fmt_temp(temperature),
            "condition": condition,
            "diff": diff_label,
            "min_temp": min_temp,
            "max_temp": max_temp,
            "feels_like": self._fmt_temp(now_fcast.get("stmpr")),
            "wind": wind_label,
            "humidity": humidity_label,
            "pm10": air_fcast.get("stationPM10Legend1"),
            "pm25": air_fcast.get("stationPM25Legend1"),
            "sunrise": self._fmt_time(sun_today.get("sriseTm")) if sun_today else None,
            "sunset": self._fmt_time(sun_today.get("ssetTm")) if sun_today else None,
        }

    # --- 코어가 호출하는 공개 메서드 ---

    def get_dashboard_data(self, db_type, limit=10):
        region_code, location, ttl, visibility = self._get_config(db_type)
        cache_key = f"weather:{region_code or location}"

        cached = self.cache_get(cache_key)
        data = None
        if cached:
            try:
                data = json.loads(cached)
            except (TypeError, ValueError):
                data = None

        if data is None:
            resolved_code = region_code or self._resolve_region_code(location)
            if resolved_code:
                html = self._fetch_weather_page(resolved_code)
                if html:
                    block_api_result = self._extract_block_api_result(html)
                    if block_api_result:
                        data = self._parse_weather(block_api_result, location)
            if data:
                self.cache_set(cache_key, json.dumps(data, ensure_ascii=False), ttl=ttl)

        if not data:
            if region_code:
                hint = "설정된 REGION_CODE가 올바른지 다시 확인해주세요."
            else:
                hint = (
                    "지역명 자동 검색이 실패했습니다. weather.naver.com에서 지역을 "
                    "직접 검색한 뒤 주소창 URL의 숫자 코드를 REGION_CODE 설정에 "
                    "입력해보세요 (예: https://weather.naver.com/today/18330600 → 18330600)."
                )
            return {
                "success": True,
                "items": [
                    {
                        "item_type": "metric",
                        "metric": "안내",
                        "value": f"'{location}' 날씨 정보를 불러오지 못했습니다.",
                        "description": hint,
                    }
                ],
            }

        # 메인 카드 하나에 날씨상태 · 온도 · 최저/최고 · 습도를 모두 묶어서 표시합니다.
        description_parts = [p for p in (data.get("condition"), data.get("diff")) if p]
        if visibility.get("range", True) and data.get("min_temp") and data.get("max_temp"):
            description_parts.append(f"최저 {data['min_temp']} 최고 {data['max_temp']}")
        if visibility.get("humidity", True) and data.get("humidity"):
            description_parts.append(f"습도 {data['humidity']}")

        items = [
            {
                "item_type": "metric",
                "metric": data["location"],
                "value": data.get("temperature") or "정보 없음",
                "description": " · ".join(description_parts),
            }
        ]

        # 나머지 정보(체감, 풍향/풍속, 미세/초미세, 일출/일몰)는 각각 별도 카드로 추가합니다.
        # 값이 없거나 설정에서 꺼둔 항목은 건너뜁니다.
        extra_fields = [
            ("feels_like", "체감", data.get("feels_like")),
            ("wind", "바람", data.get("wind")),
            ("pm10", "미세먼지", data.get("pm10")),
            ("pm25", "초미세먼지", data.get("pm25")),
            ("sunrise", "일출", data.get("sunrise")),
            ("sunset", "일몰", data.get("sunset")),
        ]
        for flag_key, label, value in extra_fields:
            if value and visibility.get(flag_key, True):
                items.append({"item_type": "metric", "metric": label, "value": value})

        return {"success": True, "items": items[: max(limit, 10)]}
