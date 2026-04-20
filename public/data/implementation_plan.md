# V4 반자동 블로거 리팩토링 계획 (2차)

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
③ Tavily가 키워드별로 관련 뉴스/컨텍스트 검색 (2단계: Search → Extract)
④ [수동 뉴스 + 프롬프트 방향성 + Tavily 보강 데이터]로 Gemini가 글 작성
⑤ 이미지 처리 (바탕화면 이미지 webp 변환)
⑥ HTML 파일로 저장 → 브라우저에서 바로 확인 가능
⑦ Tavily 참고 기사 링크를 글 하단에 자동 삽입
```

---

## User Review Required

> [!IMPORTANT]
> **Tavily 콘텐츠 추출 전략 — 2단계 접근법 제안**
>
> 조사 결과, Tavily의 **Extract API**에 `query`와 `chunks_per_source` 파라미터를 사용하면 키워드와 관련된 부분만 추출할 수 있습니다.
>
> **제안하는 흐름:**
> 1. **Search API** → 키워드로 검색, URL + 짧은 요약(`content`) 획득 (키워드당 3건)
> 2. **Extract API** → 검색된 URL들에 대해 `query=키워드`, `chunks_per_source=3`으로 호출 → 키워드 관련 핵심 단락만 추출 (청크당 최대 500자 × 3청크 = 최대 1,500자/URL)
>
> **장점:** 상위 5,000자를 무작정 자르는 것보다 키워드 관련 내용만 정확히 가져옴
> **비용:** Extract API는 5개 URL당 1~2크레딧. 키워드 8개 × 검색 3건 = 최대 24개 URL → 약 5~10크레딧 추가
>
> **대안 (단순 버전):** Search API의 `content` 필드(이미 검색어와 관련된 요약문, 약 200~500자)만 사용. Extract 호출 없이 가볍게 처리. 다만 정보량이 적을 수 있음.
>
> → **2단계(Search+Extract) 방식을 기본으로 구현하되, `--lite` 옵션을 추가해서 Extract 없이 가볍게 돌릴 수 있게** 하는 건 어떨까요?

---

## 자기비평 루프 제거에 대한 의견

맞는 판단입니다. 동일 모델 자기비평의 한계는 학계에서도 확인되고 있습니다:

- **같은 분포에서 생성 → 같은 분포에서 평가**: 모델이 자기 글을 비평하면 "자기가 좋아하는 패턴"으로 수렴합니다. 독특한 표현이나 날카로운 비유를 오히려 "부자연스럽다"고 깎아내리는 경향이 있습니다.
- **톤 평탄화(Tone Flattening)**: 비평 후 재작성하면 개성 있는 문장이 사라지고 "무난하지만 밋밋한" 글이 됩니다. 특히 구어체 톤을 지정했을 때, 자기비평이 이를 "비전문적"이라고 판단해 딱딱한 톤으로 되돌리는 경우가 많습니다.
- **유효한 경우**: 서로 다른 모델 간 비평(GPT→Claude 등) 또는 전혀 다른 시스템 프롬프트로 비평할 때만 품질 향상이 관찰됩니다.

**결론:** 자기비평 제거하고, 대신 **프롬프트 자체의 품질을 높이는 데 집중**하는 것이 효과적입니다.

---

## 더 나은 블로그 글을 위한 조언

조사 결과와 현재 글(2026-04-16-insight.mdx)을 비교 분석해서 개선 포인트를 정리했습니다.

### 현재 글의 강점 ✅
- 메타 서사 도출이 잘 됨 (흩어진 뉴스 → 큰 그림)
- 짧은 문장 호흡
- 명확한 구조 (요약 → 분석 → 결론)

### 개선 가능한 포인트

**1. "역피라미드" 구조 강화**
> 현재: 핵심 요약 3줄이 있지만 추상적. 독자가 "그래서 뭐?" 하기 쉬움.
> 개선: 첫 문장에서 **가장 충격적이거나 행동을 유발하는 결론**을 먼저 던지기.
> 예: "양자컴퓨터가 비트코인을 해킹한다? 그 전에 여러분의 은행 계좌가 먼저 털립니다." ← 이런 한 줄이 글의 운명을 결정합니다.

**2. "한 줄 Hook(갈고리)" 도입**
> 최상위 블로거들의 공통점: 첫 문장이 독자를 **붙잡습니다**. 
> 현재 글은 바로 요약으로 시작하는데, 그 앞에 **"이 글을 읽어야 하는 이유"를 1~2문장**으로 던지면 체류시간이 크게 증가합니다.
> 네이버 알고리즘도 체류시간을 중시합니다.

**3. "그래서 나는 어떻게 해야 하는데?" — 행동 지침의 구체성**
> 현재: "인내심은 가장 정교한 투자 기술입니다" → 멋있지만 모호.
> 개선: "지금 포트폴리오에서 할 일: 핵심 자산(BTC, ETH) 비중을 60% 이상 유지하고, 나머지 40%는 현금으로 대기하세요." ← 이 정도로 구체적이면 독자가 "이 블로거 진짜 실전이다"라고 느낍니다.

**4. 독자와의 대화형 장치**
> 최상위 투자 블로거들은 독자에게 **질문을 던집니다**.
> "여기서 한번 생각해보시죠", "혹시 이런 경험 있으신가요?" 
> 이 장치가 "딱딱함 → 친밀함"으로 전환하는 핵심입니다.

**5. 네이버 최적화 요소**
> - 글 끝에 **FAQ 2~3개** 추가 → 네이버 AI 브리핑 노출에 유리
> - **제목에 숫자 포함** → CTR 상승 ("3가지 이유", "5분 만에 이해하는")
> - **문장형 키워드** 활용 → 단어형보다 경쟁 낮고 전환율 높음

### 프롬프트에 반영할 개선사항

이 조언들을 AI 프롬프트에 구체적으로 녹여 넣겠습니다:

```
[글쓰기 핵심 원칙]
1. Hook: 첫 1~2문장으로 독자를 붙잡으세요. 가장 충격적이거나 반직관적인 결론을 먼저 던지세요.
2. Tone: 독자와 대화하듯 친근한 구어체 존댓말 ("~거든요", "~잖아요", "한번 생각해보시죠")
3. 구체적 행동 지침: 결론에서 "지켜보겠습니다" 금지. 구체적인 자산 배분이나 멘탈 관리 행동을 제시하세요.
4. 대화형 장치: 본문 중간에 독자에게 직접 질문을 던져 참여감을 유도하세요.
5. FAQ: 글 끝에 "자주 묻는 질문" 2~3개를 추가하세요. (네이버 AI 브리핑 노출 최적화)
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
| `extract_relevant_content(search_results, keywords)` | 검색된 URL들에 대해 Tavily Extract API 호출 (query=키워드, chunks_per_source=3) |
| `build_brain_data(folder_name, user_prompt, year)` | 전체 오케스트레이션: 수동뉴스 → 키워드추출 → 검색 → 추출 → 통합 반환 |

**반환 데이터 구조:**
```python
{
    "user_prompt": "사용자가 입력한 글 방향성",
    "vip_news": [...],           # 수동 뉴스 리스트
    "keyword_context": {         # 키워드별 Tavily 검색+추출 결과
        "FOMC 금리": [
            {"title": "...", "url": "...", "content": "키워드 관련 핵심 내용"},
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

[오늘의 핵심 속보 — 수동 뉴스]
(바탕화면 .txt 내용)

[키워드 기반 보강 데이터 — 실시간 검색 결과]
키워드 "FOMC 금리":
  - (기사 1 핵심 내용)
  - (기사 2 핵심 내용)
키워드 "달러 약세":
  - (기사 1 핵심 내용)
  ...

[글쓰기 핵심 원칙]
(톤, 구조, Hook, FAQ 등 — 아래 상세)

[글쓰기 예시]
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
가장 충격적이거나 반직관적인 결론을 먼저 던지세요. 독자가 "이거 읽어야겠다" 싶게 만드세요.

## 오늘의 핵심 요약
3개의 포인트로 요약.

## 분석과 통찰
메타 서사를 도출하세요. 뉴스 나열 금지. 숨겨진 연결고리를 찾으세요.
본문 중간에 독자에게 질문을 던져 참여감을 유도하세요.

## 결론
"지켜보겠습니다" 금지. 구체적인 자산 배분/멘탈 관리 행동 지침을 제시하세요.

## 자주 묻는 질문 (FAQ)
독자가 이 글을 읽고 궁금해할 만한 질문 2~3개와 답변을 작성하세요.

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
- **Hook 문장** 예시 추가
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
├── news_brain.py             ← [NEW] 키워드 기반 뉴스 브레인
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

## 실행 예시

```bash
cd automation
.\venv\Scripts\Activate.ps1

# 기본 사용법 (Extract API 포함)
python auto_blog.py insight "트럼프 관세 전쟁의 본질은 AI 시대의 세수 구조 전환이다. 달러 약세 → 유동성 확장 → 비트코인 수혜 흐름으로 분석"

# 가벼운 모드 (Extract API 생략, Tavily 크레딧 절약)
python auto_blog.py briefing "연준 금리 동결과 비트코인 횡보의 관계" --lite

# 결과
# → data/blog/2026-04-20-insight.html (브라우저 자동 열기)
# → public/static/images/2026/04-20-insight/ (이미지)
```

---

## Open Questions

> [!IMPORTANT]
> **1. Tavily 2단계(Search+Extract) vs 단순(Search only)**
> - 2단계를 기본으로, `--lite` 옵션으로 단순 모드 선택 가능하게 하려는데 괜찮은지?
> - 아니면 항상 한 가지 방식만 쓸지?

> [!NOTE]
> **2. 건드리지 않는 영역 (최종 확인)**
> - `fetch_market_data.py`, `fetch_liquidity_data.py` — 변경 없음
> - `.github/workflows/` — 변경 없음
> - `v3_chart_maker.py` — 삭제 안 함, import 안 함
> - 웹사이트 코드 전체 — 변경 없음

---

## Verification Plan

### Automated Tests
1. `python auto_blog.py insight "테스트 프롬프트"` → `.html` 파일 정상 생성 확인
2. 프롬프트 없이 실행 → 에러 메시지 정상 출력 확인
3. `--lite` 모드 실행 → Extract API 호출 없이 정상 동작 확인
4. 바탕화면에 `.txt` 파일 없이 실행 → 프롬프트 + Tavily만으로 글 작성 가능 확인
5. 생성된 HTML 파일을 브라우저에서 열어 렌더링 정상 확인
6. 참고 자료 링크가 글 하단에 정상 삽입되었는지 확인

### Manual Verification
- 생성된 글의 톤이 "친밀한 구어체 존댓말"인지 사용자 확인
- Hook 문장이 독자를 붙잡는 효과가 있는지 확인
- FAQ가 자연스럽게 포함되었는지 확인
- 네이버 블로그에 복사-붙여넣기 했을 때 서식 정상 확인
