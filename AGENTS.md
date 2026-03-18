# 🤖 AI 작업 가이드라인 (AGENTS.md)

> 이 파일은 AI 에이전트(Antigravity, Claude, Copilot 등)가 이 프로젝트에서 작업하기 전에 반드시 먼저 읽어야 하는 규칙 문서입니다.

---

## 📦 패키지 관리자

> ⚠️ **이 프로젝트는 `yarn`을 사용합니다. `npm install`은 절대 사용하지 마세요.**

- **패키지 설치**: `yarn add <package>` 또는 `yarn add -D <package>`
- **의존성 설치**: `yarn install`
- **빌드**: `yarn build`
- **개발 서버**: `yarn dev`

`npm install`을 사용하면 `yarn.lock`이 깨져서 GitHub Actions CI 빌드가 실패합니다.

---

## 🚀 배포 구조

- **플랫폼**: GitHub Pages
- **트리거**: `main` 브랜치에 `push` 하면 `.github/workflows/pages.yml`이 자동 실행됨
- **빌드 확인**: https://github.com/Pranger-D/crypto-oikonomos/actions
- **라이브 사이트**: https://crypto-oikonomos.vercel.app

> GitHub Pages 설정에서 Source가 **"GitHub Actions"** 로 설정되어 있어야 배포가 됩니다.
> 설정 위치: https://github.com/Pranger-D/crypto-oikonomos/settings/pages

---

## 📝 블로그 포스트 작성 규칙

### frontmatter 형식

```yaml
---
title: '제목 (작은따옴표 안에 작은따옴표 사용 금지 — 깨짐)'
date: 'YYYY-MM-DD'
tags: ['Briefing', 'Bitcoin']
draft: false
summary: 한 줄 요약
---
```

> ⚠️ **주의사항**:
> - 반드시 `---`로 열고, `---`로 닫아야 합니다 (닫는 `---` 누락 시 Contentlayer가 파일 전체를 무시)
> - `title`에 작은따옴표(`'`)가 포함된 경우 **큰따옴표(`"`)로 감싸야** 합니다
>   - 잘못된 예: `title: '트럼프의 '전략''`
>   - 올바른 예: `title: "트럼프의 '전략'"`

### 태그 (홈화면 카테고리 노출 조건)

홈화면의 Curated Collections에 나타나려면 태그가 아래 중 하나여야 합니다:

| 태그 | 설명 |
|------|------|
| `Briefing` | 시장 브리핑 |
| `Insight` | 인사이트 분석 |
| `Study` | 학습 콘텐츠 |

> 태그 목록은 `app/Main.tsx`의 `TARGET_CATEGORIES` 배열에서 관리됩니다.

---

## 🖼️ 이미지 작업 워크플로우

### 변환 도구

```bash
# 바탕화면의 blog/YYYY/MM-DD-{category} 폴더에서 이미지를 변환
python automation/archive/image_processor.py {category}
# 예: python automation/archive/image_processor.py insight
```

> 스크립트가 **오늘 날짜**로 폴더를 찾습니다. 날짜가 다르면 직접 Python으로 변환해야 합니다.

### 이미지 저장 경로

```
public/static/images/YYYY/MM-DD-{category}/{이미지명}.webp
```

### MDX에서 이미지 삽입 (권장 형식)

```jsx
<figure className="my-8 text-center">
  <Image
    alt="설명"
    src="/static/images/YYYY/MM-DD-insight/파일명.webp"
    width={800}
    height={450}
    className="mx-auto rounded-xl shadow-lg"
  />
  <figcaption className="mt-4 text-sm text-gray-500">
    그림 캡션
  </figcaption>
</figure>
```

> ⚠️ 일반 `<img>` 태그 대신 Next.js `<Image>` 컴포넌트를 사용하세요. GitHub Pages의 `BASE_PATH` 처리를 자동으로 합니다.

### 이미지 커밋 확인

이미지는 반드시 git에 추가해야 합니다:

```bash
git ls-files public/static/images/YYYY/MM-DD-{category}/
# 비어있으면 git add 필요
git add public/static/images/YYYY/MM-DD-{category}/
```

---

## 🔧 TypeScript 설정

`tsconfig.json`의 `exclude` 배열에 `automation`이 포함되어 있어야 합니다. Python 가상환경(`automation/venv/`) 내부의 `.js` 파일이 TypeScript 컴파일에 포함되면 빌드가 실패합니다.

```json
"exclude": ["node_modules", ".next", "automation", "public"]
```

---

## 🤖 자동화 파이프라인 (V3 Semi-Auto Blogger)

이 블로그의 핵심은 세 개의 Python 스크립트가 협력하는 반자동 포스팅 시스템입니다.

### 파이프라인 전체 흐름

```
[사용자가 바탕화면에 재료 준비]
    바탕화면/blog/YYYY/MM-DD-{category}/
        ├── 뉴스속보.txt      ← 핵심 속보를 복붙한 텍스트 파일들
        └── 차트이미지.png    ← 직접 캡처한 이미지들 (선택)

          ↓ python v3_auto_blogger.py {category}

① v3_news_brain.py  → 컨텍스트 수집
   - Tavily로 FOMC, 글래스노드 등 9개 고정 소스 검색 & 캐싱 (원문 30,000자 보존)
   - 바탕화면 .txt 파일 읽어서 오늘의 수동 VIP 뉴스 확보

② v3_auto_blogger.py → Gemini AI로 글 작성
   - data/core_insights.md (투자 철학)을 Few-Shot으로 주입
   - data/expert_writing_examples.md (글쓰기 예시)를 Few-Shot으로 주입
   - AI가 본문 + 차트 지시서(JSON) 동시 생성
   - 이미지 [IMAGE_파일명.webp] 플레이스홀더 자동 치환

③ v3_chart_maker.py → yfinance로 실시간 차트 생성
   - AI가 선택한 차트 타입으로 .webp 동적 차트 생성
   - public/static/images/YYYY/MM-DD-{category}/dynamic_chart_MM-DD.webp 저장

[결과물]
    data/blog/YYYY-MM-DD-{category}.mdx  ← draft: true 상태로 생성
    public/static/images/YYYY/MM-DD-{category}/  ← 이미지 저장
```

### 실행 방법

```bash
# automation/ 폴더에서 실행 (venv 활성화 필수!)
cd automation
.\venv\Scripts\Activate.ps1  # Windows

python v3_auto_blogger.py briefing   # 브리핑 카테고리
python v3_auto_blogger.py insight    # 인사이트 카테고리
python v3_auto_blogger.py study      # 스터디 카테고리
```

> ⚠️ 프로젝트 **루트 디렉토리가 아닌 `automation/` 폴더**에서 실행해야 모듈 import가 정상 작동합니다.

### 바탕화면 작업 폴더 규칙

스크립트는 **오늘 날짜**를 기준으로 아래 경로에서 재료를 자동 탐색합니다:

```
바탕화면/blog/YYYY/MM-DD-{category}/
```

폴더가 없거나 `.txt` 파일이 없어도 실행은 가능하며, 매크로 컨텍스트만으로 글을 작성합니다.

### AI 차트 타입 (v3_chart_maker.py)

AI가 JSON 지시서에 `type` 값을 지정하면 해당 차트가 생성됩니다:

| type | 설명 | 주요 파라미터 |
|------|------|----------------|
| `asset` | 단일 자산 가격 선차트 (기본값) | `ticker`, `title` |
| `compare` | 두 자산 상대 수익률 비교 | `tickers: [T1, T2]`, `aliases: [N1, N2]`, `title` |
| `ma` | 이동평균선 (20일, 50일) | `ticker`, `title` |
| `volatility` | 일일 변동폭 막대차트 | `ticker`, `title` |

### AI에 주입되는 핵심 참고 파일

| 파일 | 역할 | 수정 권장 여부 |
|------|------|----------------|
| `data/core_insights.md` | AI의 투자 철학·렌즈 17개 | ✅ 관점 업데이트 시 수정 |
| `data/expert_writing_examples.md` | Few-Shot 글쓰기 예시 | ✅ 품질 향상 시 예시 추가 |
| `automation/context_cache.json` | Tavily 컨텍스트 캐시 | ❌ 자동 관리 (수동 삭제 시 재수집) |

### 생성 결과물 후처리

스크립트 실행 후 `draft: true`로 포스팅이 생성됩니다. 아래를 확인 후 `draft: false`로 변경하고 git push:

1. `data/blog/YYYY-MM-DD-{category}.mdx` 파일 검토
2. 제목(`title:`)과 요약(`summary:`) 직접 수정
3. `draft: false`로 변경
4. `git add . && git commit -m "post: ..." && git push`

---

## ✅ 작업 전 체크리스트

AI가 이 프로젝트에서 작업을 시작하기 전에 반드시 확인하세요:

- [ ] 패키지 설치 시 `yarn` 사용 (not `npm install`)
- [ ] MDX frontmatter 형식 확인 (`---` 열고 닫기, 따옴표 규칙)
- [ ] 이미지 변환 후 `git ls-files`로 커밋 여부 확인
- [ ] 빌드 테스트: `yarn build`로 로컬 빌드 성공 확인 후 push
- [ ] 이미지 경로: `public/static/images/YYYY/MM-DD-{category}/` 구조 준수

---

## 💻 새 노트북에서 프로젝트 세팅하기

> 다른 PC/노트북에서 이 프로젝트를 처음 클론해서 작업할 때의 전체 설정 절차입니다.

### 1️⃣ 챙겨야 할 파일들 (git에 없음 — 직접 복사 필요)

아래 파일들은 `.gitignore`에 의해 git에서 제외되므로, **기존 노트북에서 직접 복사**해야 합니다.

| 파일 경로 | 용도 | 필수 여부 |
|-----------|------|-----------|
| `automation/.env` | Python 자동화 API 키 모음 | ✅ 필수 |
| `.env.local` (있을 경우) | Next.js 로컬 환경변수 (댓글/뉴스레터 연동 시) | 선택 |

#### `automation/.env` 내용 (아래 키를 새 파일에 채워야 함)

```env
TAVILY_API_KEY=...       # 뉴스 검색 AI (tavily.com)
GOOGLE_API_KEY=...       # Gemini AI 자동 블로깅
FRED_API_KEY=...         # FRED 거시지표 데이터
```

> 키를 분실했다면 각 서비스 대시보드에서 재발급:
> - Tavily: https://app.tavily.com
> - Google AI Studio: https://aistudio.google.com/apikey
> - FRED: https://fred.stlouisfed.org/docs/api/api_key.html

---

### 2️⃣ 사전 설치 — Node.js 환경

```bash
# 1. Node.js 설치 (v18 이상 권장)
#    https://nodejs.org/en/download 에서 LTS 버전 설치

# 2. Yarn 활성화 (Corepack 사용)
corepack enable
corepack prepare yarn@3.6.1 --activate

# 3. 프로젝트 루트에서 의존성 설치
yarn install

# 4. 개발 서버 실행 확인
yarn dev
```

> ⚠️ **절대 `npm install` 사용 금지** — `yarn.lock`이 깨져 CI 빌드 실패

---

### 3️⃣ 사전 설치 — Python venv 세팅

`automation/` 폴더의 Python 스크립트 전용 가상환경입니다. `venv/`는 git에 업로드되지 않으므로 **새 노트북에서 새로 생성**해야 합니다.

```bash
# 1. Python 3.10 이상 설치 확인
python --version

# 2. automation 폴더로 이동
cd automation

# 3. 가상환경 생성
python -m venv venv

# 4. 가상환경 활성화
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS / Linux:
# source venv/bin/activate

# 5. 패키지 설치
pip install -r requirements.txt
```

> `requirements.txt`는 프로젝트 루트가 아닌 `automation/` 폴더 안에 있습니다.

#### 주요 패키지 목록 (`automation/requirements.txt`)

| 패키지 | 용도 |
|--------|------|
| `google-generativeai` | Gemini AI 자동 블로깅 (v3_auto_blogger) |
| `tavily-python` | 매크로 뉴스 검색 & 캐싱 (v3_news_brain) |
| `matplotlib` | 동적 차트 렌더링 (v3_chart_maker) |
| `yfinance` | 실시간 가격 데이터 수집 (v3_chart_maker) |
| `pillow` | 이미지 webp 변환 (v3_auto_blogger) |
| `requests` / `beautifulsoup4` | 크롤링 |
| `python-dotenv` | `.env` 파일 로드 |

---

### 4️⃣ 최초 세팅 체크리스트

```
[ ] git clone https://github.com/Pranger-D/crypto-oikonomos.git
[ ] automation/.env 파일 복사 (기존 노트북에서)
[ ] Node.js + corepack + yarn install
[ ] Python venv 생성 + pip install -r automation/requirements.txt
[ ] yarn dev 실행 → http://localhost:3000 접속 확인
[ ] yarn build 한 번 실행하여 빌드 오류 없는지 확인
```

---

## 📁 주요 파일 구조

```
crypto-oikonomos/
├── app/
│   ├── Main.tsx              # 홈화면 레이아웃 (카테고리 목록 관리)
│   └── blog/page.tsx         # 블로그 목록 페이지
├── data/
│   ├── blog/                 # MDX 블로그 포스트
│   └── siteMetadata.js       # 사이트 설정
├── public/
│   └── static/images/        # 블로그 이미지 (YYYY/MM-DD-category/)
├── automation/               # Python 자동화 스크립트
│   ├── v3_auto_blogger.py    # ⭐ 메인 오케스트레이터 (여기서 실행)
│   ├── v3_news_brain.py      # ⭐ 컨텍스트 수집 & 수동 뉴스 파싱
│   ├── v3_chart_maker.py     # ⭐ AI 지시서 기반 동적 차트 생성
│   ├── .env                  # API 키 (git 제외 — 직접 복사 필요)
│   ├── context_cache.json    # Tavily 캐시 (자동 관리)
│   ├── requirements.txt      # Python 패키지 목록
│   └── archive/
│       └── image_processor.py  # 단독 이미지 변환 도구
├── contentlayer.config.ts    # 블로그 파싱 설정
├── tsconfig.json             # automation 폴더 exclude 필수
├── yarn.lock                 # yarn 사용 (npm 사용 금지)
└── .github/workflows/
    └── pages.yml             # GitHub Pages 자동 배포
```
