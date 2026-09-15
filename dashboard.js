// dashboard.js — new Function('pluginId', 'shadowRoot', 'items', <이 파일 내용>) 형태로 실행됩니다.
// shadowRoot 내부 DOM만 조작 가능합니다 (Shadow DOM 격리).

(function () {
  var data = (items && items[0]) || null;
  var root = shadowRoot;

  function el(selector) {
    return root.querySelector(selector);
  }

  function setText(field, value) {
    var target = root.querySelector('[data-f="' + field + '"]');
    if (!target) return;
    // 값은 전부 서버가 만든 숫자/단위 문자열이지만, 혹시 모를 XSS를 막기 위해
    // 항상 textContent로만 대입합니다(innerHTML 사용 안 함).
    target.textContent = (value === undefined || value === null || value === '') ? '' : value;
  }

  function setDisplay(field, visible) {
    var target = root.querySelector('[data-f="' + field + '"]');
    if (target) target.style.display = visible ? '' : 'none';
  }

  var DUST_COLOR = {
    '좋음': '#4dabf7',
    '보통': '#51cf66',
    '나쁨': '#fab005',
    '매우나쁨': '#fa5252'
  };

  function setDust(field, value) {
    setText(field, value || '정보없음');
    var dot = root.querySelector('[data-f="' + field + '-dot"]');
    if (dot) dot.style.background = DUST_COLOR[value] || '#94a3b8';
  }

  // ---- 실패 상태 처리 ----
  if (!data || data.error) {
    setText('location', (data && data.location) || '날씨 위젯');
    var body = el('.wx-body');
    if (body) body.style.display = 'none';
    var emptyEl = el('[data-f="empty"]');
    if (emptyEl) {
      emptyEl.textContent = (data && data.error) || '날씨 정보를 불러오지 못했습니다.';
      emptyEl.style.display = 'block';
    }
    return;
  }

  // ---- 아이콘 SVG (날씨 상태 + 주/야간에 따라 선택) ----
  function buildIconSvg(condition, isDaytime) {
    condition = condition || '';

    if (condition.indexOf('눈') !== -1) {
      return '<svg viewBox="0 0 64 64">' +
        '<path fill="#ced4da" d="M18 40a13 13 0 0 1 24-8 11 11 0 0 1 13 10 10 10 0 0 1-2 20H20a10 10 0 0 1-2-22z"/>' +
        '<g fill="#74c0fc"><circle cx="24" cy="50" r="2.6"/><circle cx="34" cy="54" r="2.6"/><circle cx="44" cy="50" r="2.6"/></g>' +
        '</svg>';
    }
    if (condition.indexOf('뇌') !== -1 || condition.indexOf('천둥') !== -1) {
      return '<svg viewBox="0 0 64 64">' +
        '<path fill="#adb5bd" d="M18 34a13 13 0 0 1 24-8 11 11 0 0 1 13 10 10 10 0 0 1-2 20H20a10 10 0 0 1-2-22z"/>' +
        '<path fill="#ffd43b" d="M35 34l-9 13h6.5l-4.5 9 13-15h-6.5z"/>' +
        '</svg>';
    }
    if (condition.indexOf('비') !== -1 || condition.indexOf('소나기') !== -1) {
      return '<svg viewBox="0 0 64 64">' +
        '<path fill="#adb5bd" d="M18 32a13 13 0 0 1 24-8 11 11 0 0 1 13 10 10 10 0 0 1-2 20H20a10 10 0 0 1-2-22z"/>' +
        '<g stroke="#4dabf7" stroke-width="3" stroke-linecap="round">' +
        '<line x1="24" y1="48" x2="20" y2="58"/><line x1="34" y1="48" x2="30" y2="58"/><line x1="44" y1="48" x2="40" y2="58"/>' +
        '</g></svg>';
    }
    if (condition.indexOf('흐림') !== -1) {
      return '<svg viewBox="0 0 64 64">' +
        '<path fill="#ced4da" d="M16 40a13 13 0 0 1 24-8 11 11 0 0 1 13 10 10 10 0 0 1-2 20H18a10 10 0 0 1-2-22z"/>' +
        '</svg>';
    }
    if (condition.indexOf('구름많') !== -1) {
      return isDaytime
        ? '<svg viewBox="0 0 64 64">' +
          '<circle cx="22" cy="22" r="10" fill="#ffd43b"/>' +
          '<path fill="#ced4da" d="M18 44a13 13 0 0 1 24-8 11 11 0 0 1 13 10 10 10 0 0 1-2 20H20a10 10 0 0 1-2-22z"/>' +
          '</svg>'
        : '<svg viewBox="0 0 64 64">' +
          '<path fill="#adb5bd" d="M32 14a10 10 0 1 0 7 17.2 8 8 0 0 1-7-17.2z"/>' +
          '<path fill="#ced4da" d="M16 46a13 13 0 0 1 24-8 11 11 0 0 1 13 10 10 10 0 0 1-2 20H18a10 10 0 0 1-2-22z"/>' +
          '</svg>';
    }
    if (condition.indexOf('구름조금') !== -1) {
      return isDaytime
        ? '<svg viewBox="0 0 64 64">' +
          '<circle cx="26" cy="24" r="14" fill="#ffd43b"/>' +
          '<path fill="#e9ecef" d="M20 46a11 11 0 0 1 20-6 9 9 0 0 1 11 8 8 8 0 0 1-2 17H22a8 8 0 0 1-2-19z"/>' +
          '</svg>'
        : '<svg viewBox="0 0 64 64">' +
          '<path fill="#748ffc" d="M28 12a14 14 0 1 0 11.5 21.9A11 11 0 0 1 28 12z"/>' +
          '<circle cx="44" cy="16" r="2.4" fill="#ffe066"/>' +
          '<path fill="#e9ecef" d="M20 46a11 11 0 0 1 20-6 9 9 0 0 1 11 8 8 8 0 0 1-2 17H22a8 8 0 0 1-2-19z"/>' +
          '</svg>';
    }

    // 맑음 (기본값)
    if (isDaytime) {
      return '<svg viewBox="0 0 64 64">' +
        '<g stroke="#ffd43b" stroke-width="3.2" stroke-linecap="round">' +
        '<line x1="32" y1="3" x2="32" y2="11"/><line x1="32" y1="53" x2="32" y2="61"/>' +
        '<line x1="3" y1="32" x2="11" y2="32"/><line x1="53" y1="32" x2="61" y2="32"/>' +
        '<line x1="11" y1="11" x2="17" y2="17"/><line x1="47" y1="47" x2="53" y2="53"/>' +
        '<line x1="11" y1="53" x2="17" y2="47"/><line x1="47" y1="17" x2="53" y2="11"/>' +
        '</g><circle cx="32" cy="32" r="13.5" fill="#ffd43b"/>' +
        '</svg>';
    }
    return '<svg viewBox="0 0 64 64">' +
      '<path fill="#748ffc" d="M38 11a20.5 20.5 0 1 0 14.6 31A16.5 16.5 0 0 1 38 11z"/>' +
      '<path fill="#ffe066" d="M50 13.5l1.7 3.9 4.2 0.6-3 3 0.7 4.2-3.6-2.1-3.6 2.1 0.7-4.2-3-3 4.2-0.6z"/>' +
      '</svg>';
  }

  // ---- 공통 필드 바인딩 ----
  setText('location', data.location);
  setText('today', data.today_label || '');
  setText('temperature', data.temp_num != null ? data.temp_num : '-');
  setText('condition', data.condition || '정보 없음');
  setText('diff', data.diff || '');
  setText('min_temp', data.min_temp || '-');
  setText('max_temp', data.max_temp || '-');
  setText('feels_like', data.feels_like || '-');
  setText('wind_dir', data.wind_dir || '바람');
  setText('wind_speed', data.wind_speed || '-');
  setText('humidity', data.humidity || '-');
  setDust('pm10', data.pm10);
  setDust('pm25', data.pm25);
  setText('sunrise', data.sunrise || '-');
  setText('sunset', data.sunset || '-');

  var iconEl = el('[data-f="icon"]');
  if (iconEl) iconEl.innerHTML = buildIconSvg(data.condition, data.is_daytime !== false);

  // 값이 없는 항목은 그리드/행 자체를 숨깁니다.
  setDisplay('range-row', !!(data.min_temp && data.max_temp));
  setDisplay('stat-feels', !!data.feels_like);
  setDisplay('stat-wind', !!(data.wind_dir || data.wind_speed));
  setDisplay('stat-humidity', !!data.humidity);
  setDisplay('stat-dust', !!(data.pm10 || data.pm25));
  setDisplay('stat-sun', !!(data.sunrise || data.sunset));

  // ---- 표시 방식 분기 ----
  var listEl = el('[data-f="list"]');

  if (data.display_mode === 'general') {
    // GENERAL: 풀 비주얼 블록을 감추고 항목별 리스트만 보여줍니다.
    ['.wx-badge-wrap', '.wx-main', '.wx-condition-row', '.wx-range-row', '.wx-stats'].forEach(function (sel) {
      var block = el(sel);
      if (block) block.style.display = 'none';
    });
    if (listEl) {
      listEl.style.display = 'flex';
      listEl.innerHTML = '';
      var rows = data.general_rows || [];
      rows.forEach(function (row) {
        var li = document.createElement('li');
        var left = document.createElement('span');
        left.textContent = row.label;
        var right = document.createElement('span');
        right.textContent = row.value;
        li.appendChild(left);
        li.appendChild(right);
        listEl.appendChild(li);
      });
    }
  } else if (listEl) {
    listEl.style.display = 'none';
  }
})();
