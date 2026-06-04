# 배포 가이드 (사이트로 올리기)

이 프로젝트는 두 부분으로 나뉩니다.

| 부분 | 위치 | 어디서 실행 |
|------|------|-------------|
| **카테고리 수집(스크래핑)** | `scraper.py` / `main.py` | 내 컴퓨터(로컬)에서만 (실제 Chrome 필요, 쿠팡 차단 우회) |
| **사이트(추첨 UI)** | `web/` (정적 HTML+JS) | Vercel / Netlify / GitHub Pages 어디든 |

> 사이트는 `web/data.json`(수집·필터링된 스냅샷)만 읽어서 브라우저에서 랜덤 추첨합니다.
> 서버가 필요 없어 정적 호스팅이면 다 됩니다.

---

## 데이터 갱신 → 재배포 흐름

쿠팡 카테고리가 바뀌면 로컬에서 갱신 후 다시 push 하면 됩니다.

```bash
source .venv/bin/activate
python main.py fetch     # 쿠팡에서 최신 카테고리 수집 (Chrome 창 잠깐 뜸)
python build_web.py      # 필터 적용 → web/data.json 갱신
git add categories.json web/data.json
git commit -m "데이터 갱신"
git push                 # 연결돼 있으면 Vercel이 자동 재배포
```

필터 기준(`filters.py`)을 바꿨을 때도 `python build_web.py` 만 다시 돌리면 됩니다.

---

## 방법 A) Vercel (추천)

### A-1. GitHub에 올리고 Vercel과 연결 (자동 재배포)

1. GitHub에서 새 저장소 생성 (예: `coupang-category-picker`).
2. 로컬에서 연결 후 push:
   ```bash
   git remote add origin https://github.com/<사용자명>/coupang-category-picker.git
   git branch -M main
   git push -u origin main
   ```
3. https://vercel.com → **Add New → Project → 방금 저장소 Import**
4. 설정:
   - **Root Directory**: `web`  ← 꼭 이렇게 (정적 사이트 폴더)
   - **Framework Preset**: Other
   - Build Command / Output Directory: 비워둠
5. **Deploy** → 끝. `https://<프로젝트>.vercel.app` 주소가 생깁니다.

### A-2. Vercel CLI로 바로 (GitHub 없이)

```bash
npm i -g vercel
cd web
vercel        # 로그인 후 안내 따라가면 배포됨
vercel --prod # 운영 배포
```

---

## 방법 B) Netlify

1. GitHub에 push (위 A-1의 1~2단계).
2. Netlify → Add new site → Import → 저장소 선택.
3. **Base directory**: `web`, Build command 비움, **Publish directory**: `web`.

---

## 방법 C) GitHub Pages

Pages는 루트나 `/docs` 폴더만 지원하므로, `web/` 대신 `docs/`로 빌드하거나
`web/` 내용을 `gh-pages` 브랜치로 올리면 됩니다. (필요하면 안내 추가)
