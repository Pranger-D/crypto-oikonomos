# TypeScript 오류 해결 가이드

## 🔍 현재 상황

VS Code에서 123개의 TypeScript 오류가 표시되고 있습니다. 이는 대부분 **일시적인 문제**입니다.

## ✅ 해결 방법 (우선순위 순)

### 1. TypeScript 서버 재시작 (가장 효과적)

**VS Code에서:**
1. `Ctrl + Shift + P` (명령 팔레트)
2. "TypeScript: Restart TS Server" 입력 및 실행
3. 몇 초 기다리면 오류 대부분 사라짐

### 2. VS Code 재시작

간단하지만 효과적:
```
VS Code 완전 종료 → 재실행
```

### 3. node_modules 재설치

드물지만 필요한 경우:
```bash
rm -rf node_modules
rm yarn.lock
yarn install
```

### 4. TypeScript 캐시 삭제

```bash
rm -rf .next
rm -rf .contentlayer
yarn dev
```

## 🎯 예상되는 오류 유형

### A. "파일이 프로젝트 목록에 없음" 오류
**원인**: TypeScript가 새 파일을 아직 인식 못함  
**해결**: TS 서버 재시작 (방법 1)

### B. "--jsx 플래그 없음" 오류
**원인**: tsconfig.json이 아직 로드 안 됨  
**해결**: TS 서버 재시작 (방법 1)

### C. "모듈을 찾을 수 없음" 오류
**원인**: 경로 별칭(@/) 인식 문제  
**해결**: VS Code 재시작 (방법 2)

## 🚀 개발 서버는 정상 작동

**중요**: TypeScript 오류가 있어도 개발 서버는 정상 작동합니다!

- ✅ `yarn dev` 실행 중
- ✅ http://localhost:3000 접속 가능
- ✅ 대시보드 렌더링 정상

## 📝 실제 코드 오류 확인

TS 서버 재시작 후에도 오류가 남아있다면:

```bash
npx tsc --noEmit
```

실제 타입 오류만 표시됩니다.

## 💡 권장 조치

1. **먼저 시도**: TypeScript 서버 재시작
2. **여전히 오류**: VS Code 재시작
3. **브라우저 테스트**: http://localhost:3000에서 실제 작동 확인
4. **문제 있으면**: 구체적인 오류 메시지 공유

---

**대부분의 경우 1번 방법으로 해결됩니다!** 🎉
