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

## ✅ 작업 전 체크리스트

AI가 이 프로젝트에서 작업을 시작하기 전에 반드시 확인하세요:

- [ ] 패키지 설치 시 `yarn` 사용 (not `npm install`)
- [ ] MDX frontmatter 형식 확인 (`---` 열고 닫기, 따옴표 규칙)
- [ ] 이미지 변환 후 `git ls-files`로 커밋 여부 확인
- [ ] 빌드 테스트: `yarn build`로 로컬 빌드 성공 확인 후 push
- [ ] 이미지 경로: `public/static/images/YYYY/MM-DD-{category}/` 구조 준수

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
│   └── archive/
│       └── image_processor.py  # 이미지 변환 도구
├── contentlayer.config.ts    # 블로그 파싱 설정
├── tsconfig.json             # automation 폴더 exclude 필수
├── yarn.lock                 # yarn 사용 (npm 사용 금지)
└── .github/workflows/
    └── pages.yml             # GitHub Pages 자동 배포
```
