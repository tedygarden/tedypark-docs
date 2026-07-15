from __future__ import annotations

import json
import re
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
CONTENT = json.loads((ROOT / "content" / "apps.json").read_text(encoding="utf-8"))
APPS = {app["slug"]: app for app in CONTENT["apps"]}

EXPECTED_BUNDLES = {
    "asanagram": "app.tedypark.asanagram",
    "madang": "app.tedypark.heimdall",
    "moksori": "app.tedypark.moksori",
    "walkmin": "com.tedypark.walkmin.walklab",
    "quaddo": "app.tedypark.quaddo",
    "seoulbuilder": "app.tedypark.seoulbuilder",
    "oneulai": "app.tedypark.oneulai",
}
EXPECTED_ALIASES = {"heimdall": "madang", "seoul-builder": "seoulbuilder"}
ACTION_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.uses: list[tuple[str, dict[str, str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag in {"a", "link"} and values.get("href"):
            self.links.append(values["href"])
        self.uses.append((tag, values))


def html_files() -> list[Path]:
    return sorted(SITE.rglob("*.html"))


def deletion_route(slug: str) -> str:
    return "delete-account" if slug == "oneulai" else "data-deletion"


def canonical_files() -> list[Path]:
    files = [SITE / "index.html", SITE / "support/index.html", SITE / "legal/privacy/index.html", SITE / "legal/terms/index.html"]
    for slug, app in APPS.items():
        for route in ("", "privacy", "support", deletion_route(slug)):
            files.append(SITE / slug / route / "index.html")
        if app.get("terms"):
            files.append(SITE / slug / "terms/index.html")
    return files


class ManifestTests(unittest.TestCase):
    def test_fixed_operator_contact_and_date(self) -> None:
        self.assertEqual(CONTENT["operator"], "tedyway 운영자")
        self.assertEqual(CONTENT["contact"], "hi.k.ai@icloud.com")
        self.assertEqual(CONTENT["effective_date"], "2026-07-15")

    def test_app_and_bundle_matrix_is_exact(self) -> None:
        self.assertEqual(set(APPS), set(EXPECTED_BUNDLES))
        self.assertEqual({slug: app["bundle_id"] for slug, app in APPS.items()}, EXPECTED_BUNDLES)

    def test_alias_matrix_is_exact_and_has_no_collision(self) -> None:
        actual: dict[str, str] = {}
        for slug, app in APPS.items():
            for alias in app["aliases"]:
                self.assertNotIn(alias, APPS)
                self.assertNotIn(alias, actual)
                actual[alias] = slug
        self.assertEqual(actual, EXPECTED_ALIASES)

    def test_required_content_fields_are_nonempty(self) -> None:
        required = {
            "name", "bundle_id", "platforms", "tagline", "overview", "account",
            "local_data", "apple_services", "external_services", "retention",
            "deletion_steps", "deletion_limits", "support_notes", "evidence",
        }
        for slug, app in APPS.items():
            with self.subTest(slug=slug):
                self.assertFalse(required - app.keys())
                for key in required:
                    self.assertTrue(app[key])


class GeneratedSiteTests(unittest.TestCase):
    def test_generator_is_deterministic_and_current(self) -> None:
        result = subprocess.run(
            ["python3", "scripts/generate_site.py", "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_expected_page_structure_exists(self) -> None:
        expected = set(canonical_files())
        for alias, target in EXPECTED_ALIASES.items():
            routes = ("", "privacy", "support", "data-deletion")
            for route in routes:
                expected.add(SITE / alias / route / "index.html")
        self.assertEqual(set(html_files()), expected)
        self.assertEqual(len(expected), 41)

    def test_canonical_pages_have_identity_date_and_exact_contact(self) -> None:
        for path in canonical_files():
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn("tedyway 운영자", text)
                self.assertIn("2026-07-15", text)
                self.assertIn("hi.k.ai@icloud.com", text)
                self.assertIn('lang="ko"', text)
                self.assertIn("Generated from content/apps.json", text)

    def test_each_app_page_contains_exact_bundle(self) -> None:
        for slug, bundle in EXPECTED_BUNDLES.items():
            routes = ("", "privacy", "support", deletion_route(slug))
            for route in routes:
                path = SITE / slug / route / "index.html"
                with self.subTest(path=path.relative_to(ROOT)):
                    self.assertIn(bundle, path.read_text(encoding="utf-8"))
        self.assertIn(
            EXPECTED_BUNDLES["oneulai"],
            (SITE / "oneulai/terms/index.html").read_text(encoding="utf-8"),
        )

    def test_aliases_redirect_to_canonical_pages(self) -> None:
        for alias, canonical in EXPECTED_ALIASES.items():
            for route in ("", "privacy", "support", "data-deletion"):
                path = SITE / alias / route / "index.html"
                parser = LinkParser()
                parser.feed(path.read_text(encoding="utf-8"))
                canonical_links = [attrs.get("href", "") for tag, attrs in parser.uses if tag == "link" and attrs.get("rel") == "canonical"]
                self.assertEqual(len(canonical_links), 1, path)
                resolved = (path.parent / unquote(canonical_links[0])).resolve()
                expected = (SITE / canonical / route).resolve()
                self.assertEqual(resolved, expected)

    def test_all_local_links_and_stylesheets_resolve(self) -> None:
        for path in html_files():
            parser = LinkParser()
            parser.feed(path.read_text(encoding="utf-8"))
            for href in parser.links:
                parsed = urlsplit(href)
                if parsed.scheme in {"http", "https", "mailto"} or href.startswith("#"):
                    continue
                target = (path.parent / unquote(parsed.path)).resolve()
                if parsed.path.endswith("/") or target.is_dir():
                    target = target / "index.html"
                with self.subTest(source=path.relative_to(ROOT), href=href):
                    self.assertTrue(target.is_file(), f"broken link: {path} -> {href} ({target})")

    def test_no_placeholder_or_stale_identity_remains(self) -> None:
        joined = "\n".join(path.read_text(encoding="utf-8") for path in html_files())
        content_source = (ROOT / "content/apps.json").read_text(encoding="utf-8")
        for forbidden in (
            "TODO_", "TODO SUPPORT", "support@tedypark.com", "privacy@tedypark.com",
            "support@tedypark.app", 'Tedypark(&quot;회사&quot;)', "2026-04-02", "2026년 4월 13일",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, joined)
                self.assertNotIn(forbidden, content_source)
        mail_addresses = set(re.findall(r"mailto:([^\"?]+)", joined))
        self.assertEqual(mail_addresses, {"hi.k.ai@icloud.com"})

    def test_external_links_are_https(self) -> None:
        for path in html_files():
            parser = LinkParser()
            parser.feed(path.read_text(encoding="utf-8"))
            for href in parser.links:
                parsed = urlsplit(href)
                if parsed.netloc:
                    with self.subTest(path=path.relative_to(ROOT), href=href):
                        self.assertEqual(parsed.scheme, "https")

        generated = (ROOT / "scripts/generate_site.py").read_text(encoding="utf-8")
        self.assertNotIn("https://www.apple.com/legal/privacy/ko/", generated)
        self.assertIn("https://www.apple.com/legal/privacy/kr/", generated)

    def test_asanagram_discloses_full_content_spotlight_and_missing_cleanup(self) -> None:
        privacy = (SITE / "asanagram/privacy/index.html").read_text(encoding="utf-8")
        deletion = (SITE / "asanagram/data-deletion/index.html").read_text(encoding="utf-8")
        for required in (
            "태스크 이름·설명",
            "댓글 본문",
            "AI 생성 결과",
            "최대 2,000개",
            "Core Spotlight",
            "만료일 없이",
        ):
            self.assertIn(required, privacy)
        for required in ("Core Spotlight", "색인 전체 삭제 버튼", "opt-in"):
            self.assertIn(required, deletion)

    def test_moksori_discloses_opt_in_transfer_and_release_blocker(self) -> None:
        text = (SITE / "moksori/privacy/index.html").read_text(encoding="utf-8")
        for required in (
            "speech.platform.bing.com", "명시적으로 동의", "실험적 비공식 연동",
            "정확한 보관 기간", "해결 전 프로덕션 출시는 차단",
        ):
            self.assertIn(required, text)
        self.assertIn("마이크·연락처·위치 권한을 요청하지 않습니다", text)

    def test_oneulai_discloses_temporary_video_and_incomplete_purge(self) -> None:
        privacy = (SITE / "oneulai/privacy/index.html").read_text(encoding="utf-8")
        deletion = (SITE / "oneulai/delete-account/index.html").read_text(encoding="utf-8")
        terms = (SITE / "oneulai/terms/index.html").read_text(encoding="utf-8")
        for required in (
            "Supabase Storage", "임시 업로드", "고아 객체", "purge worker",
            "즉시 삭제를 주장하지 않습니다", "새 TestFlight·App Store 업로드를 모두 차단",
            "260613.203453", "legacy build", "Firebase Remote Config",
        ):
            self.assertIn(required, privacy)
        for required in ("앱의 설정", "HTTP 202", "삭제 완료가 아닙니다", "고정 완료 기한"):
            self.assertIn(required, deletion)
        self.assertIn("AI 결과는 오류나 누락이 있을 수 있으며 의료·발달·교육 진단", terms)
        self.assertIn("새 TestFlight·App Store 업로드를 하지 않습니다", terms)

    def test_no_account_apps_and_icloud_boundary_are_explicit(self) -> None:
        for slug in ("moksori", "walkmin", "seoulbuilder"):
            text = (SITE / slug / deletion_route(slug) / "index.html").read_text(encoding="utf-8")
            self.assertIn("계정", text)
            self.assertIn("이메일", text)
        for slug in ("asanagram", "madang", "quaddo"):
            text = (SITE / slug / deletion_route(slug) / "index.html").read_text(encoding="utf-8")
            self.assertIn("private CloudKit", text)
            self.assertIn("앱 삭제", text)


    def test_deletion_path_contract_and_no_cross_app_support_leakage(self) -> None:
        self.assertTrue((SITE / "oneulai/delete-account/index.html").is_file())
        self.assertFalse((SITE / "oneulai/data-deletion/index.html").exists())
        for slug in EXPECTED_BUNDLES:
            if slug == "oneulai":
                continue
            self.assertTrue((SITE / slug / "data-deletion/index.html").is_file())
            self.assertFalse((SITE / slug / "delete-account/index.html").exists())
            support = (SITE / slug / "support/index.html").read_text(encoding="utf-8")
            self.assertNotIn("오늘아이", support)
            self.assertNotIn("계정 삭제는 앱 설정에서 시작", support)
            for other_slug, other_app in APPS.items():
                if other_slug != slug:
                    self.assertNotIn(other_app["name"], support)


class WorkflowTests(unittest.TestCase):
    def _assert_immutable_actions(self, workflow: Path) -> None:
        text = workflow.read_text(encoding="utf-8")
        refs = re.findall(r"uses:\s*([^\s]+)@([^\s#]+)", text)
        self.assertTrue(refs, workflow)
        for action, ref in refs:
            with self.subTest(workflow=workflow.name, action=action):
                self.assertRegex(ref, ACTION_SHA_RE)

    def test_deploy_is_main_only_and_pinned(self) -> None:
        workflow = ROOT / ".github/workflows/deploy.yml"
        text = workflow.read_text(encoding="utf-8")
        self._assert_immutable_actions(workflow)
        self.assertIn("- main", text)
        self.assertIn("if: github.ref == 'refs/heads/main'", text)
        self.assertNotIn("- sol", text)
        self.assertIn("timeout-minutes: 10", text)
        self.assertIn("persist-credentials: false", text)

    def test_sol_validation_workflow_is_pinned(self) -> None:
        workflow = ROOT / ".github/workflows/validate.yml"
        text = workflow.read_text(encoding="utf-8")
        self._assert_immutable_actions(workflow)
        self.assertIn("- sol", text)
        self.assertIn("make check", text)
        self.assertNotIn("pages: write", text)
        self.assertNotIn("deploy-pages", text)
        self.assertIn("timeout-minutes: 5", text)
        self.assertIn("persist-credentials: false", text)


if __name__ == "__main__":
    unittest.main()
