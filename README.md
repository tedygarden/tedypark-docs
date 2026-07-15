# tedyway 앱 정책·지원 사이트

이 저장소는 **앱마다 다른 데이터 흐름과 삭제 경계를 숨기지 않고 공개하는 단일 정책 사이트**다. `content/apps.json`을 원본으로 정적 HTML을 생성하며, `main`만 GitHub Pages에 배포한다. `sol`은 검증만 수행하고 배포하지 않는다.

## 포함 앱

| 앱 | 공개 경로 | 번들 ID | 계정 |
|---|---|---|---|
| Asanagram | `/asanagram/` | `app.tedypark.asanagram` | tedyway 계정 없음, Asana PAT 사용 |
| 마당 | `/madang/` | `app.tedypark.heimdall` | 없음; 선택적 private CloudKit |
| 목소리 | `/moksori/` | `app.tedypark.moksori` | 없음 |
| Walkmin | `/walkmin/` | `com.tedypark.walkmin.walklab` | 없음; 선택적 Game Center |
| Quad Do | `/quaddo/` | `app.tedypark.quaddo` | 없음; 선택적 private CloudKit |
| SeoulBuilder | `/seoulbuilder/` | `app.tedypark.seoulbuilder` | 없음 |
| 오늘아이 | `/oneulai/` | `app.tedypark.oneulai` | Sign in with Apple 또는 이메일 |

기존 이름 호환을 위해 `/heimdall/`은 `/madang/`으로, `/seoul-builder/`는 `/seoulbuilder/`로 이동한다. 각 앱에는 다음 문서가 있다.

- 앱 안내: `/<slug>/`
- 개인정보처리방침: `/<slug>/privacy/`
- 지원: `/<slug>/support/`
- 서비스 계정이 없는 앱의 데이터 삭제: `/<slug>/data-deletion/`
- 오늘아이 계정·데이터 삭제: `/oneulai/delete-account/`
- 오늘아이 이용약관: `/oneulai/terms/`

운영 주체는 `tedyway 운영자`, 시행일은 `2026-07-15`, 모니터링할 공개 연락처는 `hi.k.ai@icloud.com` 하나로 고정했다.

## 수정 방법

생성된 `site/**/*.html`을 직접 수정하지 않는다.

```bash
# 1. 앱별 사실 수정
$EDITOR content/apps.json

# 2. 정적 페이지 재생성
make generate

# 3. 생성물·내부 링크·연락처·시행일·번들 ID·CI 계약 검증
make check
```

생성기는 Python 표준 라이브러리만 사용한다. 테스트는 로컬 링크, 별칭, 외부 HTTPS, placeholder·오래된 연락처, 중요한 개인정보 문구와 모든 GitHub Action의 40자리 commit SHA 고정을 검사한다.

## 배포 원칙

- `.github/workflows/validate.yml`: `sol` push와 `main` 대상 PR에서 `make check`만 실행한다.
- `.github/workflows/deploy.yml`: `main` push 또는 `main`에서 수동 실행할 때만 Pages를 배포한다. job-level ref gate가 `sol` 배포를 차단한다.
- `sol`에서 Pages 배포, `main` 병합, 법적 승인 완료 표시는 하지 않는다.
- 실제 공개 전 [근거와 수동 검토 게이트](docs/source-evidence.md)를 모두 확인한다.

## 중요한 미완료 사항

- **오늘아이**: 활성 내부 TestFlight `1.0 (260613.203453)`은 direct Gemini/Firebase가 남은 legacy 흐름이라 다음 `sol` 계약과 같다고 간주하지 않는다. legacy 회수·정책 정합성, 동영상 임시 Storage 고아 객체 정리와 계정 삭제 purge worker E2E 증거가 끝날 때까지 새 TestFlight·App Store 업로드를 모두 차단한다. 삭제 요청 `202 Accepted`를 완료로 표현하지 않는다.
- **목소리**: `speech.platform.bing.com` 비공식 연동의 독립 앱 사용 허가와 처리·보관 범위가 확인되지 않았다. 해결 전 프로덕션 출시를 차단한다.
- **Asanagram·마당·Quad Do**: 앱 안에서 로컬과 private CloudKit을 한 번에 지우는 기능이 없다. 앱 삭제와 iCloud 삭제를 같은 것으로 안내하지 않는다.
- 이 문서는 코드·설정 근거를 반영한 공학 초안이다. 법률 자문이나 App Store 승인 보장이 아니며 공개 전 운영자·연락처·법적 의무를 사람이 다시 검토해야 한다.
