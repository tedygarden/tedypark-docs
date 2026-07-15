# 정책 근거와 공개 전 수동 검토 게이트

요약: 페이지는 2026-07-15 `sol` 구현과 배포 설정에서 확인한 사실만 반영했다. 확인하지 못한 국가, 제공자 보관 기간, DPA 체결, 삭제 완료 기한이나 보증을 만들지 않았다. **코드 검증은 법률 검토를 대체하지 않으며, 아래 수동 게이트를 통과하기 전 `main`에 공개하면 안 된다.**

## 공식 기준

### Apple

- [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/): 지원 URL의 정확한 연락처, 완전하고 정확한 메타데이터, 개인정보·보안과 계정 삭제 요구를 공개 전 다시 확인한다.
- [Manage app privacy](https://developer.apple.com/help/app-store-connect/manage-app-information/manage-app-privacy/): App Store Connect의 App Privacy 답변을 앱·SDK·정책의 실제 데이터 흐름과 일치시킨다.
- [Offering account deletion in your app](https://developer.apple.com/support/offering-account-deletion-in-your-app): 계정 생성을 지원하는 오늘아이는 앱 안에서 삭제 시작점을 제공해야 한다. 일반 삭제 경로를 이메일만으로 대체하지 않는다.
- [App Privacy Details](https://developer.apple.com/app-store/app-privacy-details/): 앱 코드뿐 아니라 제3자 SDK와 제공자 처리까지 포함해 답변한다. Apple이 직접 관리하는 데이터와 개발자가 받는 데이터를 구분한다.

### 대한민국 개인정보 기준

- [개인정보 보호법 제21조(개인정보의 파기)](https://www.law.go.kr/법령/개인정보보호법/제21조)
- [개인정보 보호법 제30조(개인정보 처리방침의 수립 및 공개)](https://www.law.go.kr/법령/개인정보보호법/제30조)
- [개인정보 보호법 제36조(개인정보의 정정·삭제)](https://www.law.go.kr/법령/개인정보보호법/제36조)
- [개인정보 보호법 제37조(개인정보의 처리정지 등)](https://www.law.go.kr/법령/개인정보보호법/제37조)
- [개인정보 처리방침 작성지침(2025.4.) — 개인정보보호위원회](https://www.privacy.go.kr/front/bbs/bbsView.do?bbsNo=BBSMSTR_000000000049&bbscttNo=20806)

법령·지침의 최신성, 서비스에 실제 적용되는 조항, 운영자 표시와 국외 이전 고지는 공개 직전 전문가 또는 책임자가 다시 판단한다.

## 앱별 구현 근거 스냅샷

아래 경로는 정책 저장소와 나란히 감사한 각 앱의 `sol` worktree 기준이다. 원본 코드를 정책 저장소로 복사하지 않았다.

| 앱 / 번들 ID | 확인한 경계 | 주요 근거 |
|---|---|---|
| Asanagram / `app.tedypark.asanagram` | Asana PAT는 Keychain, 피드 캐시는 로컬, 개인 상태는 private CloudKit, 선택적 macOS AI는 설치된 CLI 경유. Core Spotlight는 기기별 기본 OFF opt-in이며 같은 도메인을 삭제 후 최대 2,000개로 교체 | `asanagram-sol/README.md`, `Asanagram.entitlements`, `Sources/Kit/AIService.swift`, `FeedStore+Sync.swift`, `Spotlight.swift`, `SpotlightPrivacyPolicy.swift`, `FeedStore.swift`, `TokenStore.swift`, `RootView.swift` |
| 마당 / `app.tedypark.heimdall` | 공개 커뮤니티 URLSession·WKWebView, 기본 WebKit 쿠키, 글 보관본 로컬+private CloudKit, 개발자 백엔드 없음 | `heimdall-sol/docs/specs/0002-cloudkit-sync.md`, `0006-sol-reader-hardening.md`, `SiteRegistry.swift`, `WebFallbackView.swift` |
| 목소리 / `app.tedypark.moksori` | 시스템·Personal Voice는 기기, 문구·히스토리는 SwiftData/App Group, opt-in 때 문장을 Bing speech endpoint로 보내고 MP3 캐시 | `moksori-sol/docs/privacy-contract.md`, `docs/release/privacy-review-checklist.md`, `EdgeTTS.swift`, 앱 Privacy manifest |
| Walkmin / `com.tedypark.walkmin.walklab` | Core Motion·사용 중 위치·PhotoKit·로컬 알림·Game Center, 게임/걸음은 로컬, 위치 자취는 메모리 | `picmin-sol/Docs/Reports/2026-07-14-sol-privacy-contract.md`, `WalkLocationProvider.swift`, `GameCenterService.swift`, Privacy manifest |
| Quad Do / `app.tedypark.quaddo` | SwiftData/App Group/private CloudKit, Reminders·StoreKit·Keychain UUID, Firebase Remote Config는 실제 plist가 있을 때만 활성화 | `quaddo-sol/README.md`, `QuadDo.entitlements`, `SharedModelContainer.swift`, `FirebaseBootstrap.swift` |
| SeoulBuilder / `app.tedypark.seoulbuilder` | 약 100m 사용 중 위치는 메모리, 도시 상태는 Documents JSON, 별점은 UserDefaults, 런타임 네트워크·계정 없음 | `seoul-builder-sol/Project.swift`, `LocationService.swift`, `CitySave.swift`, `Stage.swift` |
| 오늘아이 / `app.tedypark.oneulai` | Apple/email 로그인, 아동·가족·동의·미디어·AI·기기·구매 데이터, Supabase Auth/DB/Storage/Edge→Gemini, deletion 202 후 purge 미완료 | `onl-ai-sol/docs/audits/2026-07-15-sol-ai-proxy-privacy.md`, `APIEndpoints.swift`, `request-account-deletion`, `analyze-child-video` Edge functions |

## 공개 전 반드시 사람이 확인할 항목

1. **운영 주체와 연락처**
   - `tedyway 운영자`라는 표시가 실제 법적·세무상 운영 형태에 맞는지 확인한다.
   - `hi.k.ai@icloud.com`의 수신·답장·스팸함을 실제로 시험하고 지원 책임자를 정한다.
   - 존재하지 않거나 모니터링하지 않는 `@tedypark.com`, 회사명, 주소를 만들지 않는다.
2. **앱 안 접근성과 URL**
   - 각 배포 바이너리 설정 화면에서 해당 개인정보처리방침과 지원·삭제 URL을 쉽게 열 수 있는지 실기기로 확인한다.
   - App Store Connect의 Support URL·Privacy Policy URL이 정확한 앱 경로이고 HTTPS로 공개되는지 확인한다.
3. **App Privacy와 바이너리**
   - archive Privacy Report, 포함된 SDK·entitlement·네트워크 캡처를 다시 보고 App Privacy 답변과 문구를 맞춘다.
   - 빌드 시 주입되는 설정 파일이나 SDK가 저장소 감사와 다르면 정책을 먼저 갱신한다.
4. **계정 삭제**
   - 오늘아이 앱 안 시작 → 202 접수 → 계정 동결 → Auth/DB/Storage/Edge/푸시/세션 purge → 재시도·실패 큐 → 완료 상태를 운영 환경에서 끝까지 증명한다.
   - 삭제 완료 전에는 완료 메일·완료 화면·고정 처리 기한을 약속하지 않는다.
   - Apple Photos, iCloud, App Store 거래처럼 운영자가 지울 수 없는 영역을 사용자에게 분리해 알린다.
   - 활성 내부 TestFlight `1.0 (260613.203453)`의 direct Gemini/Firebase legacy 흐름을 회수·만료하거나 별도 정책으로 검증하기 전에는 새 개인정보 입력과 신규 업로드를 중지한다.
5. **오늘아이 아동·미디어 처리**
   - 운영 Supabase migration/RLS/Edge 배포, provider 자격 회전, 접근 로그, 보호자·수집·국외 이전 동의 증거를 확인한다.
   - 동영상 임시 Storage의 정상·오류·중단·고아 객체 청소와 계정 삭제 연계를 증명한다.
   - 실제 배포 지역, 재위탁, 제공자 보관 기간과 법적 근거는 계약·콘솔 증거 후에만 구체적으로 추가한다.
6. **목소리 온라인 음성**
   - 독립 앱에서 `speech.platform.bing.com` endpoint를 쓰는 현행 약관·라이선스·상표 근거 또는 서면 허가를 확보한다.
   - 전송 문장·IP·요청 메타데이터의 처리 지역·기간·재위탁을 확인한다. 확인하지 못하면 프로덕션에서 온라인 기능을 제거하거나 비활성화한다.
7. **Apple private 데이터 삭제 UX**
   - Asanagram·마당·Quad Do의 전체 로컬/Keychain/private CloudKit 삭제 기능 부재를 제품 백로그 P0/P1로 유지한다.
   - 앱 삭제만으로 private CloudKit·Keychain 자료도 삭제된다고 안내하지 않는다.
   - Asanagram의 Core Spotlight 기본 OFF·동의·삭제·재시도·토큰 교체 경로는 시뮬레이터 단위 테스트만으로 완료로 간주하지 않고, 실제 iOS·macOS 기기에서 색인 생성·만료·삭제와 검색 결과 열기 차단을 확인한다.
8. **최종 법률·문안 검토**
   - 실제 수집 항목, 목적, 제3자, 보관, 삭제, 정보주체 권리, 아동·국외 이전 고지를 운영 증거와 대조한다.
   - 개인정보보호 책임자 표시, 처리 기한, 이전 국가, DPA 또는 보안 보증은 증거와 법적 검토 없이 추가하지 않는다.
   - 승인자는 시행일과 App Store 제출 버전을 기록한다.

## 자동 검증 범위와 한계

`make check`는 생성물 일치, 내부 링크, bundle ID, 시행일, 단일 연락처, 중요 blocker 문구와 immutable GitHub Actions를 검사한다. 다음은 자동 검증하지 않는다.

- 메일함이 실제로 모니터링되는지
- 외부 사이트와 제공자 정책의 현재 내용
- App Store Connect App Privacy 답변
- 배포 바이너리의 실제 SDK·네트워크
- 한국 또는 다른 지역 법률의 구체적 적용
- Supabase·CloudKit·Microsoft·Google의 운영 환경 삭제 완료

따라서 green CI는 법률 승인이나 출시 승인이 아니다.
