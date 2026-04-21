# V4 반자동 블로거 리팩토링 계획 (피드백 반영 최종안)

## 배경 및 목적

기존 `v3_auto_blogger.py` + `v3_news_brain.py` 파이프라인을 완전히 새로 설계합니다.

**핵심 변경:**
- 고정 컨텍스트 캐싱 9개 소스 → **사용자 프롬프트 기반 키워드 실시간 검색**으로 전환
- 온라인 블로그 발행 중단 → **네이버 블로그 초안용** HTML 파일 출력
- 차트 생성 기능 제거
- 자기비평 루프 제거

### 새로운 흐름

```
python auto_blog.py {category} "글의 방향성 프롬프트"

          ↓

① 바탕화면 수동 뉴스(.txt) 읽기
② Gemini가 [프롬프트 + 수동 뉴스]에서 핵심 키워드 5~8개 추출
③ Tavily가 키워드별로 관련 데이터 검색 (2단계: Search → Extract)
④ Python이 추출 콘텐츠를 스마트 트림 (5000자 기준)
⑤ [수동 뉴스(주재료) + 프롬프트 방향성 + Tavily 보강 데이터(보완재)]로 Gemini가 글 작성
⑥ 이미지 처리 (바탕화면 이미지 webp 변환)
⑦ HTML 파일로 저장 → 브라우저에서 바로 확인 가능
⑧ Tavily 참고 기사 링크를 글 하단에 자동 삽입
```

---

## 핵심 설계 결정 (피드백 반영)

### 1. Tavily 콘텐츠 추출 — 스마트 트림 전략

> [!IMPORTANT]
> **원칙: 원본 보존 우선, 긴 글만 키워드 근방 문단 추출**

**2단계 흐름:**
1. **Search API** → 키워드로 검색, URL + 짧은 요약(`content`) 획득 (키워드당 3건)
2. **Extract API** → 검색된 URL들에서 `raw_content`(전문) 추출 (query/chunks_per_source 미사용 → 전문 획득)

**Python 스마트 트림 로직 (Extract 결과에 적용):**

```python
def smart_trim(raw_content: str, keyword: str, max_chars: int = 5000) -> str:
    """
    - raw_content <= 5000자: 원본 그대로 반환 (요약/가공 없음)
    - raw_content > 5000자: 키워드 포함 문단 + 주변 문단을 조합하여 ~5000자로 트림
    """
    if len(raw_content) <= max_chars:
        return raw_content  # 짧은 글은 손대지 않음
    
    paragraphs = raw_content.split('\n\n')
    
    # 1. 키워드가 포함된 문단의 인덱스 찾기
    keyword_indices = [i for i, p in enumerate(paragraphs) if keyword.lower() in p.lower()]
    
    if not keyword_indices:
        # 키워드가 없으면 앞에서부터 5000자
        return raw_content[:max_chars]
    
    # 2. 키워드 문단 중심으로 주변 문단 확장
    selected = set()
    for idx in keyword_indices:
        # 키워드 문단 + 앞뒤 2개 문단씩 포함 (맥락 확보)
        for offset in range(-2, 3):
            neighbor = idx + offset
            if 0 <= neighbor < len(paragraphs):
                selected.add(neighbor)
    
    # 3. 순서 유지하면서 조합, 5000자 이내로 제한
    result_parts = []
    char_count = 0
    for i in sorted(selected):
        part = paragraphs[i]
        if char_count + len(part) > max_chars:
            break
        result_parts.append(part)
        char_count += len(part)
    
    return '\n\n'.join(result_parts)
```

**핵심:**
- 5000자 이하 콘텐츠 → **원본 그대로** AI에게 전달 (요약하면 정보 손실)
- 5000자 초과 콘텐츠 → 키워드가 등장하는 문단 + **앞뒤 2개 문단**(맥락 확보) → ~5000자로 조합
- 주변 문단이 전체적인 맥락을 설명할 가능성이 높으므로 핵심 단락만 뽑는 것보다 효과적

**`--lite` 모드:** Extract API 호출을 건너뛰고 Search API의 `content` 필드만 사용. Tavily 크레딧 절약용.

---

### 2. 수동 뉴스 = 주재료, Tavily = 보완재

> [!IMPORTANT]
> **수동 뉴스가 글의 중심축이고, Tavily 검색 결과는 보조 참고 자료**

프롬프트에서 이 역할 구분을 명확히 합니다:

```
[오늘의 핵심 속보 — 수동 뉴스 (이것이 글의 주재료입니다)]
(바탕화면 .txt 내용)

[키워드 기반 보강 데이터 — 보완 참고용]
아래는 키워드로 검색한 보조 자료입니다. 주재료를 뒷받침하거나 맥락을 넓히는 용도로만 활용하세요.
수동 뉴스와 충돌하면 수동 뉴스를 우선하세요.
```

Tavily 검색 결과의 시간 제한은 두지 않습니다. 과거 자료가 맥락에 유용할 수도 있고, 너무 최신으로 제한하면 관련 없는 결과가 나올 수 있으므로 Tavily 기본 설정에 맡깁니다.

---

### 3. 행동 지침(투자 조언) 제거

> [!WARNING]
> **투자 관련 구체적 조언은 책임 문제가 있으므로 제거**

기존 계획에 있던 아래 내용을 **삭제**합니다:
- ~~"구체적인 자산 배분이나 멘탈 관리 행동을 제시하세요"~~
- ~~"지금 포트폴리오에서 할 일: 핵심 자산(BTC, ETH) 비중을 60% 이상 유지하고..."~~

**대신:** 결론에서는 통찰의 함의를 정리하되, 구체적 매수/매도/비중 조언은 하지 않습니다. 면책조항은 기존처럼 글 하단에 유지합니다.

---

### 4. Hook — 균형 잡힌 톤

역피라미드 구조와 Hook 문장은 유지하되, **어그로성 방지** 가이드를 프롬프트에 추가합니다:

```
## Hook (1~2문장)
핵심 결론이나 반직관적 시각을 먼저 던져 독자의 관심을 끄세요.
단, 과장("충격!", "대폭락 임박!")이나 선정적 표현은 금지합니다.
전문가다운 절제된 톤으로, 읽고 싶게 만드세요.
```

---

### 5. 글쓰기 예시 — 참고용 명시

`expert_writing_examples.md`는 **서식(##, div, br 등)의 참고 예시**임을 프롬프트에서 명확히 합니다. AI가 이 톤이나 길이에 과적합하지 않도록:

```
[글쓰기 서식 예시 (참고용)]
아래는 서식(## 헤딩, div 래퍼, <br/> 줄바꿈)의 사용법을 보여주는 참고 예시입니다.
글의 톤, 길이, 관점은 이 예시에 묶이지 말고 자유롭게 쓰되, 서식 규칙만 정확히 따르세요.
```

---

## Proposed Changes

### Component 1: 새로운 뉴스 브레인 모듈

#### [NEW] [news_brain.py](file:///d:/Project/crypto-oikonomos/automation/news_brain.py)

기존 `v3_news_brain.py`를 완전히 대체합니다.

**함수 구성:**

| 함수 | 역할 |
|------|------|
| `fetch_manual_news(folder_name, year)` | 바탕화면 `.txt` 파일 읽기 (기존과 동일) |
| `extract_keywords(user_prompt, manual_news)` | Gemini에게 프롬프트+뉴스 입력 → 키워드 5~8개 JSON 배열 추출 |
| `search_by_keywords(keywords)` | 키워드별 Tavily Search API 호출 (키워드당 max_results=3) |
| `extract_and_trim(search_results, keywords)` | Tavily Extract API로 전문 추출 → `smart_trim()`으로 5000자 기준 스마트 트림 |
| `smart_trim(raw_content, keyword, max_chars=5000)` | 5000자 이하는 원본 그대로, 초과 시 키워드 근방 문단+주변 문단 조합 |
| `build_brain_data(folder_name, user_prompt, year)` | 전체 오케스트레이션: 수동뉴스 → 키워드추출 → 검색 → 추출+트림 → 통합 반환 |

**반환 데이터 구조:**
```python
{
    "user_prompt": "사용자가 입력한 글 방향성",
    "vip_news": [...],           # 수동 뉴스 리스트 (주재료)
    "keyword_context": {         # 키워드별 Tavily 검색+추출 결과 (보완재)
        "FOMC 금리": [
            {
                "title": "...",
                "url": "...",
                "content": "스마트 트림 적용된 원문 (최대 5000자)"
            },
            ...
        ],
        ...
    },
    "reference_links": [         # 참고 자료 링크 (글 하단용)
        {"title": "...", "url": "..."},
        ...
    ]
}
```

**`--lite` 모드:** Extract API 호출을 건너뛰고 Search API의 `content` 필드만 사용. Tavily 크레딧 절약용.

---

### Component 2: 메인 오케스트레이터

#### [NEW] [auto_blog.py](file:///d:/Project/crypto-oikonomos/automation/auto_blog.py)

**CLI 인터페이스:**
```bash
# 기본 사용법
python auto_blog.py insight "트럼프 관세 전쟁의 본질은 AI 시대의 세수 구조 전환"

# Tavily Extract 생략 (가벼운 모드)
python auto_blog.py insight "프롬프트 내용" --lite

# 과거 날짜 테스트
python auto_blog.py insight "프롬프트 내용" --date 2026-04-15

# 프롬프트 없이 실행 → 에러
python auto_blog.py insight
# → "❌ 글의 방향성 프롬프트를 입력해주세요."
```

**주요 함수 구성:**

| 함수 | 역할 |
|------|------|
| `process_manual_images(...)` | 바탕화면 이미지 webp 변환 (기존 유지) |
| `generate_blog_content(brain_data, image_list)` | Gemini에게 프롬프트+뉴스+컨텍스트 전달 → 블로그 본문 생성 |
| `build_html_output(blog_body, metadata, ref_links)` | 마크다운 본문 → 스타일링된 HTML 변환 |
| `run_automation()` | 메인 오케스트레이터 |

**프롬프트 구조 (Gemini에게 전달):**
```
[글의 방향성 — 사용자 프롬프트]
"트럼프 관세 전쟁의 본질은..."

[투자 철학 렌즈]
(core_insights.md 내용)

[오늘의 핵심 속보 — 수동 뉴스 (이것이 글의 주재료입니다)]
(바탕화면 .txt 내용)

[키워드 기반 보강 데이터 — 보완 참고용]
아래는 키워드로 검색한 보조 자료입니다. 주재료를 뒷받침하거나 맥락을 넓히는 용도로만 활용하세요.
수동 뉴스와 충돌하면 수동 뉴스를 우선하세요.
키워드 "FOMC 금리":
  - (기사 1 원문/트림 내용)
  - (기사 2 원문/트림 내용)
키워드 "달러 약세":
  - (기사 1 원문/트림 내용)
  ...

[글쓰기 핵심 원칙]
(톤, 구조, Hook 등 — 아래 상세)

[글쓰기 서식 예시 (참고용)]
아래는 서식(## 헤딩, div 래퍼, <br/> 줄바꿈)의 사용법을 보여주는 참고 예시입니다.
글의 톤, 길이, 관점은 이 예시에 묶이지 말고 자유롭게 쓰되, 서식 규칙만 정확히 따르세요.
(expert_writing_examples.md 내용)

[이미지 매칭 지시]
(사용 가능한 이미지 목록)

[참고 자료 링크]
(Tavily 검색 링크 — 글 하단에 삽입할 것)
```

**톤앤매너 프롬프트 (핵심 변경):**
```
당신은 전문 투자 블로거입니다. 독자와 카페에서 대화하듯 친근하게 쓰되, 전문성은 절대 잃지 마세요.

[톤 규칙]
- "~거든요", "~잖아요", "~인 거죠" 같은 부드러운 구어체 존댓말을 자연스럽게 섞으세요.
- 독자에게 직접 질문을 던지는 대화형 장치를 활용하세요 ("한번 생각해보시죠", "여기서 핵심은요").
- "~ㅋㅋ", "~요ㅎㅎ" 같은 지나친 캐주얼은 금지. 전문가의 품격을 유지하세요.
- 이모티콘 금지.

[구조]
## Hook (1~2문장)
핵심 결론이나 반직관적 시각을 먼저 던져 독자의 관심을 끄세요.
단, 과장("충격!", "대폭락 임박!")이나 선정적 표현은 금지합니다.
전문가다운 절제된 톤으로, 읽고 싶게 만드세요.

## 오늘의 핵심 요약
3개의 포인트로 요약.

## 분석과 통찰
메타 서사를 도출하세요. 뉴스 나열 금지. 숨겨진 연결고리를 찾으세요.
본문 중간에 독자에게 질문을 던져 참여감을 유도하세요.

## 결론
통찰의 함의를 정리하되, 구체적인 매수/매도/비중 조언은 하지 마세요.
"지켜보겠습니다" 같은 무의미한 마무리도 피하세요.
"이 흐름이 의미하는 것은 ~입니다" 식으로 독자가 스스로 판단할 수 있는 시각을 제공하세요.

## 자주 묻는 질문 (FAQ)
독자가 이 글을 읽고 궁금해할 만한 질문 2~3개와 답변을 작성하세요. (네이버 AI 브리핑 노출 최적화)

## 참고 자료
(시스템 자동 삽입 — AI가 작성하지 않음)
```

**HTML 출력 스타일:**
- 깔끔한 단일 HTML 파일 (외부 CSS/JS 의존 없음)
- 인라인 CSS로 가독성 높은 타이포그래피
- 밝은 배경, 적절한 여백, 모바일 반응형
- 이미지는 `<img>` 태그로 상대 경로 삽입
- 마크다운 → HTML 변환은 Python `markdown` 라이브러리 사용
- 저장 경로: `data/blog/YYYY-MM-DD-{category}.html`
- 저장 후 브라우저에서 자동 열기 (`os.startfile()`)

---

### Component 3: 차트 생성 모듈

#### ~~v3_chart_maker.py~~ — 사용 안 함
- `auto_blog.py`에서 import하지 않음
- 파일은 삭제하지 않고 그대로 둠 (다른 용도로 쓸 수 있으므로)

---

### Component 4: 글쓰기 예시 업데이트

#### [MODIFY] [expert_writing_examples.md](file:///d:/Project/crypto-oikonomos/data/expert_writing_examples.md)

- 웹 전용 서식(`<div>`, `<br/>` 등) **언급 자체를 제거** (금지 규칙도 쓰지 않음)
- 순수 마크다운 예시로 전면 교체
- **구어체 존댓말** 톤으로 예시 재작성
- **Hook 문장** 예시 추가 (절제된 톤)
- **FAQ 섹션** 예시 추가
- 서식 원칙을 마크다운 기준으로 단순화

예시 변경 전/후:

```diff
- SOFR 금리가 4.18%를 기록했습니다.<br/>
- 연준의 기준선(IORB, 4.15%)을 기어코 뚫고 올라간 겁니다.
+ SOFR 금리가 4.18%를 찍었거든요.
+ 연준의 기준선인 4.15%를 뚫고 올라간 거죠.
+
+ 고작 0.03%p 차이라고요? 그런데 이게 생각보다 심각한 신호입니다.
```

---

### Component 5: 기존 파일 처리

| 파일 | 처리 |
|------|------|
| `v3_auto_blogger.py` | `archive/`로 이동 |
| `v3_news_brain.py` | `archive/`로 이동 |
| `context_cache.json` (104KB) | 삭제 |
| `v3_chart_maker.py` | 그대로 둠 (auto_blog.py에서 사용 안 함) |

---

### Component 6: requirements.txt 확인

#### [MODIFY] [requirements.txt](file:///d:/Project/crypto-oikonomos/automation/requirements.txt)

- `markdown` 패키지 추가 필요 (마크다운 → HTML 변환용)
- 기존 패키지는 유지

---

## 전체 파일 구조 (변경 후)

```
automation/
├── auto_blog.py              ← [NEW] 메인 오케스트레이터
├── news_brain.py             ← [NEW] 키워드 기반 뉴스 브레인 (스마트 트림 포함)
├── v3_chart_maker.py         ← [KEEP] 미사용, 삭제 안 함
├── fetch_market_data.py      ← [KEEP] 코인게코 (변경 없음)
├── fetch_liquidity_data.py   ← [KEEP] FRED (변경 없음)
├── .env                      ← [KEEP]
├── requirements.txt          ← [MODIFY] markdown 패키지 추가
├── archive/
│   ├── v3_auto_blogger.py    ← [MOVE]
│   ├── v3_news_brain.py      ← [MOVE]
│   ├── run_automation.py     ← [KEEP]
│   └── image_processor.py    ← [KEEP]
```

---

## 건드리지 않는 영역 (확인 완료)

- `fetch_market_data.py`, `fetch_liquidity_data.py` — 변경 없음
- `.github/workflows/` — 변경 없음
- `v3_chart_maker.py` — 삭제 안 함, import 안 함
- 웹사이트 코드 전체 — 변경 없음

---

## 실행 예시

```bash
cd automation
.\venv\Scripts\Activate.ps1

# 기본 사용법 (Extract API 포함, 스마트 트림 적용)
python auto_blog.py insight "트럼프 관세 전쟁의 본질은 AI 시대의 세수 구조 전환이다. 달러 약세 → 유동성 확장 → 비트코인 수혜 흐름으로 분석"

# 가벼운 모드 (Extract API 생략, Tavily 크레딧 절약)
python auto_blog.py briefing "연준 금리 동결과 비트코인 횡보의 관계" --lite

# 결과
# → data/blog/2026-04-20-insight.html (브라우저 자동 열기)
# → public/static/images/2026/04-20-insight/ (이미지)
```

---

## Verification Plan

### Automated Tests
1. `python auto_blog.py insight "테스트 프롬프트"` → `.html` 파일 정상 생성 확인
2. 프롬프트 없이 실행 → 에러 메시지 정상 출력 확인
3. `--lite` 모드 실행 → Extract API 호출 없이 정상 동작 확인
4. 바탕화면에 `.txt` 파일 없이 실행 → 프롬프트 + Tavily만으로 글 작성 가능 확인
5. `smart_trim()` 유닛 테스트:
   - 5000자 이하 입력 → 원본 그대로 반환
   - 10000자 입력 + 키워드 → 키워드 근방 문단 + 주변 문단 포함, ~5000자 반환
   - 키워드 미매칭 → 앞에서부터 5000자 반환
6. 생성된 HTML 파일을 브라우저에서 열어 렌더링 정상 확인
7. 참고 자료 링크가 글 하단에 정상 삽입되었는지 확인

### Manual Verification
- 생성된 글의 톤이 "친밀한 구어체 존댓말"인지 사용자 확인
- Hook 문장이 절제되면서도 관심을 끄는지 확인
- FAQ가 자연스럽게 포함되었는지 확인
- **구체적 투자 조언(비중 %, 매수/매도)이 없는지** 확인
- 네이버 블로그에 복사-붙여넣기 했을 때 서식 정상 확인
