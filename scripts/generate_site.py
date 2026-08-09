#!/usr/bin/env python3
"""Generate the static policy site from content/apps.json using only stdlib."""

from __future__ import annotations

import argparse
import html
import json
import posixpath
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
CONTENT_PATH = ROOT / "content" / "apps.json"
SITE_ROOT = ROOT / "site"
GENERATED_MARKER = "Generated from content/apps.json; edit the source, not this file."

PROVIDER_LINKS: dict[str, list[tuple[str, str]]] = {
    "asanagram": [
        ("Asana 개인정보 안내", "https://asana.com/terms/privacy-statement"),
        ("Apple 개인정보 보호", "https://www.apple.com/legal/privacy/kr/"),
        ("GitHub 개인정보 안내", "https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement"),
    ],
    "madang": [("Apple 개인정보 보호", "https://www.apple.com/legal/privacy/kr/")],
    "moksori": [
        ("Microsoft Edge 데이터·개인정보 안내", "https://learn.microsoft.com/legal/microsoft-edge/privacy"),
        ("Apple 개인정보 보호", "https://www.apple.com/legal/privacy/kr/"),
    ],
    "walkmin": [("Apple 개인정보 보호", "https://www.apple.com/legal/privacy/kr/")],
    "quaddo": [
        ("Apple 개인정보 보호", "https://www.apple.com/legal/privacy/kr/"),
        ("Google 개인정보처리방침", "https://policies.google.com/privacy?hl=ko"),
    ],
    "seoulbuilder": [("Apple 개인정보 보호", "https://www.apple.com/legal/privacy/kr/")],
    "oneulai": [
        ("Apple 개인정보 보호", "https://www.apple.com/legal/privacy/kr/"),
        ("Supabase 개인정보 안내", "https://supabase.com/privacy"),
        ("Google Gemini API 이용약관", "https://ai.google.dev/terms"),
        ("Google 개인정보처리방침", "https://policies.google.com/privacy?hl=ko"),
    ],
}


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_content() -> dict[str, Any]:
    with CONTENT_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def relative_href(current_file: str, target_directory: str) -> str:
    current_directory = posixpath.dirname(current_file) or "."
    target = target_directory.rstrip("/") or "."
    result = posixpath.relpath(target, current_directory)
    return ("./" if result == "." else result + "/")


def external_link(label: str, url: str) -> str:
    return (
        f'<a href="{escape(url)}" rel="noopener noreferrer">{escape(label)}</a>'
    )


def list_html(items: Iterable[str]) -> str:
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def effective_date(app: dict[str, Any], content: dict[str, Any]) -> str:
    return str(app.get("effective_date", content["effective_date"]))


def metadata_rows(app: dict[str, Any], content: dict[str, Any]) -> str:
    rows = [
        ("앱", app["name"]),
        ("번들 ID", app["bundle_id"]),
        ("플랫폼", app["platforms"]),
        ("운영 주체", content["operator"]),
        ("시행일", effective_date(app, content)),
    ]
    return '<dl class="metadata">' + "".join(
        f"<div><dt>{escape(key)}</dt><dd>{escape(value)}</dd></div>" for key, value in rows
    ) + "</dl>"


def deletion_route(app: dict[str, Any]) -> str:
    return "delete-account" if app["slug"] == "oneulai" else "data-deletion"


def nav_html(current_file: str, app: dict[str, Any], include_terms: bool = False) -> str:
    slug = app["slug"]
    links = [
        ("앱 안내", slug),
        ("개인정보처리방침", f"{slug}/privacy"),
        ("지원", f"{slug}/support"),
        ("데이터 삭제", f"{slug}/{deletion_route(app)}"),
    ]
    if include_terms:
        links.insert(2, ("이용약관", f"{slug}/terms"))
    links.append(("전체 앱", ""))
    return '<nav class="nav" aria-label="문서 탐색">' + "".join(
        f'<a href="{escape(relative_href(current_file, target))}">{escape(label)}</a>'
        for label, target in links
    ) + "</nav>"


def page(
    *,
    current_file: str,
    title: str,
    description: str,
    body: str,
    lang: str = "ko",
    robots: str | None = None,
    head_extra: str = "",
) -> str:
    stylesheet = posixpath.relpath("styles.css", posixpath.dirname(current_file) or ".")
    robots_meta = f'\n    <meta name="robots" content="{escape(robots)}" />' if robots else ""
    head_extra_block = f"    {head_extra}\n" if head_extra else ""
    return f"""<!doctype html>
<html lang="{escape(lang)}">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="{escape(description)}" />{robots_meta}
    <title>{escape(title)}</title>
    <link rel="stylesheet" href="{escape(stylesheet)}" />
{head_extra_block}  </head>
  <body>
    <!-- {GENERATED_MARKER} -->
    <main class="shell">
      {body}
    </main>
  </body>
</html>
"""


def heading(app: dict[str, Any], title: str, eyebrow: str) -> str:
    return f"""<p class="eyebrow">{escape(app['name'])} · {escape(eyebrow)}</p>
<h1>{escape(title)}</h1>"""


def notice_html(app: dict[str, Any]) -> str:
    notice = app.get("notice")
    if not notice:
        return ""
    return f'<aside class="notice" role="note"><strong>출시 상태 고지</strong><p>{escape(notice)}</p></aside>'


def app_landing(app: dict[str, Any], content: dict[str, Any]) -> tuple[str, str]:
    current_file = f"{app['slug']}/index.html"
    body = f"""<article class="doc">
{heading(app, app['name'], '정책·지원')}
<p class="lead">{escape(app['tagline'])}</p>
<p>{escape(app['overview'])}</p>
{notice_html(app)}
{metadata_rows(app, content)}
<h2>계정</h2>
<p>{escape(app['account'])}</p>
<h2>데이터 경계 한눈에 보기</h2>
<div class="card-grid">
  <section class="card"><h3>기기 안</h3><p>{escape(app['local_data'][0])}</p></section>
  <section class="card"><h3>Apple 영역</h3><p>{escape(app['apple_services'][0])}</p></section>
  <section class="card"><h3>외부 서비스</h3><p>{escape(app['external_services'][0])}</p></section>
</div>
<p class="muted">앱 삭제, 운영자 서버 삭제, Apple 또는 외부 제공자 데이터 삭제는 서로 같은 작업이 아닐 수 있습니다. 이 앱에 실제로 해당하는 범위는 개인정보처리방침과 데이터 삭제 안내를 확인하세요.</p>
{nav_html(current_file, app, include_terms=bool(app.get('terms')))}
<footer>{escape(content['operator'])} · <a href="mailto:{escape(content['contact'])}">{escape(content['contact'])}</a> · 시행일 {escape(effective_date(app, content))}</footer>
</article>"""
    return current_file, page(
        current_file=current_file,
        title=f"{app['name']} 정책·지원",
        description=app["tagline"],
        body=body,
    )


def app_privacy(app: dict[str, Any], content: dict[str, Any]) -> tuple[str, str]:
    current_file = f"{app['slug']}/privacy/index.html"
    links = PROVIDER_LINKS[app["slug"]]
    body = f"""<article class="doc">
{heading(app, '개인정보처리방침', 'Privacy')}
<p class="summary"><strong>요약:</strong> 이 문서는 {escape(app['name'])}의 현재 구현에서 데이터가 기기, Apple 서비스, 외부 제공자 중 어디에서 처리되는지 구분합니다. 확인되지 않은 보관 기간이나 삭제 보장은 만들지 않습니다.</p>
{notice_html(app)}
{metadata_rows(app, content)}
<h2>1. 적용 범위와 계정</h2>
<p>{escape(app['overview'])}</p>
<p>{escape(app['account'])}</p>
<h2>2. 기기에서 처리·보관하는 데이터</h2>
{list_html(app['local_data'])}
<h2>3. Apple 서비스와 private 데이터 경계</h2>
{list_html(app['apple_services'])}
<h2>4. 외부 서비스와 전송</h2>
{list_html(app['external_services'])}
<p class="source-links">제공자 문서: {" · ".join(external_link(label, url) for label, url in links)}</p>
<h2>5. 이용 목적</h2>
<p>위 데이터는 각 항목에 적은 앱 기능과 사용자의 선택을 처리하는 데 사용됩니다. 이 앱에 존재하지 않는 계정·동기화 목적이나 현재 구현에서 확인되지 않은 광고·추적·판매 목적을 이 문서가 새로 부여하지 않습니다.</p>
<h2>6. 보관</h2>
{list_html(app['retention'])}
<h2>7. 삭제와 사용자 선택</h2>
{list_html(app['deletion_steps'])}
{list_html(app['deletion_limits'])}
<p><a class="button-link" href="{escape(relative_href(current_file, app['slug'] + '/' + deletion_route(app)))}">데이터 삭제 안내 보기</a></p>
<h2>8. 권리와 문의</h2>
<p>사용자는 적용되는 법령에 따라 자신의 정보에 대한 열람, 정정·삭제, 처리 정지 또는 동의 철회를 문의할 수 있습니다. Apple 또는 위에 적은 외부 제공자가 직접 관리하는 영역은 해당 제공자의 설정과 정책도 함께 사용해야 합니다.</p>
<p>문의: <a href="mailto:{escape(content['contact'])}">{escape(content['contact'])}</a>. 민감한 원문, 비밀번호, 인증 토큰, 정확한 위치나 아동 미디어는 메일에 넣지 마세요.</p>
<h2>9. 변경과 공개 전 확인</h2>
<p>앱의 실제 데이터 흐름이 바뀌면 이 문서와 App Store Connect의 App Privacy 답변을 함께 갱신해야 합니다. 공개 배포 전 운영자 연락처 수신 여부, 앱 안 정책 링크, 삭제 동작과 제3자 정책을 사람이 다시 검토합니다.</p>
{nav_html(current_file, app, include_terms=bool(app.get('terms')))}
<footer>{escape(content['operator'])} · 시행일 {escape(effective_date(app, content))}</footer>
</article>"""
    return current_file, page(
        current_file=current_file,
        title=f"{app['name']} 개인정보처리방침",
        description=f"{app['name']} 개인정보 처리와 삭제 경계",
        body=body,
    )


def app_support(app: dict[str, Any], content: dict[str, Any]) -> tuple[str, str]:
    current_file = f"{app['slug']}/support/index.html"
    body = f"""<article class="doc">
{heading(app, '지원', 'Support')}
<p class="summary"><strong>지원 채널:</strong> <a href="mailto:{escape(content['contact'])}">{escape(content['contact'])}</a></p>
{notice_html(app)}
{metadata_rows(app, content)}
<h2>문의할 때 알려 주세요</h2>
<ul>
  <li>앱 이름과 버전</li>
  <li>기기 모델과 운영체제 버전</li>
  <li>문제가 발생한 화면과 재현 순서</li>
  <li>오류 문구와 발생 시각</li>
</ul>
<h2>{escape(app['name'])} 확인 사항</h2>
{list_html(app['support_notes'])}
<h2>개인정보·삭제 문의</h2>
<p>먼저 <a href="{escape(relative_href(current_file, app['slug'] + '/' + deletion_route(app)))}">데이터 삭제 안내</a>에 적은 현재 제공 절차와 Apple·제3자 경계를 확인하세요.</p>
{('<p>오늘아이 계정 삭제는 앱 설정에서 시작하며 메일은 일반 삭제의 유일한 시작점이 아닙니다.</p>' if app['slug'] == 'oneulai' else '<p>이 앱은 tedyway 서비스 계정을 만들지 않으므로 이메일로 계정 삭제를 요청할 대상이 없습니다.</p>')}
<h2>보안</h2>
<p>비밀번호, 인증 토큰 등 민감정보를 메일에 보내지 마세요. 위 앱별 확인 사항에 적은 민감 데이터는 가리고, 가능한 경우 임의의 재현 데이터와 비식별 화면을 사용하세요.</p>
{nav_html(current_file, app, include_terms=bool(app.get('terms')))}
<footer>{escape(content['operator'])} · <a href="mailto:{escape(content['contact'])}">{escape(content['contact'])}</a> · 시행일 {escape(effective_date(app, content))}</footer>
</article>"""
    return current_file, page(
        current_file=current_file,
        title=f"{app['name']} 지원",
        description=f"{app['name']} 사용자 지원과 문의 안내",
        body=body,
    )


def app_deletion(app: dict[str, Any], content: dict[str, Any]) -> tuple[str, str]:
    current_file = f"{app['slug']}/{deletion_route(app)}/index.html"
    title = "계정 및 데이터 삭제" if app["slug"] == "oneulai" else "데이터 삭제 안내"
    body = f"""<article class="doc">
{heading(app, title, 'Deletion')}
<p class="summary"><strong>계정 상태:</strong> {escape(app['account'])}</p>
{notice_html(app)}
{metadata_rows(app, content)}
<h2>삭제·정리 순서</h2>
<ol>{''.join(f'<li>{escape(item)}</li>' for item in app['deletion_steps'])}</ol>
<h2>삭제되지 않거나 별도 조치가 필요한 영역</h2>
{list_html(app['deletion_limits'])}
<h2>보관 경계</h2>
{list_html(app['retention'])}
<h2>지원</h2>
<p>상태 확인이나 접근 문제는 <a href="mailto:{escape(content['contact'])}">{escape(content['contact'])}</a>으로 문의하세요. 메일에는 비밀번호, 인증 토큰, 정확한 위치, 아동 미디어 또는 업무 원문을 넣지 마세요.</p>
<p class="muted">서비스 계정이 없는 앱은 이메일로 ‘계정 삭제’를 요청할 대상이 없습니다. Apple 또는 외부 제공자가 직접 관리하는 영역과 앱 로컬 자료는 운영자 서버와 서로 분리될 수 있습니다. 이 앱에 해당하는 범위는 위 안내를 따르세요.</p>
{nav_html(current_file, app, include_terms=bool(app.get('terms')))}
<footer>{escape(content['operator'])} · 시행일 {escape(effective_date(app, content))}</footer>
</article>"""
    return current_file, page(
        current_file=current_file,
        title=f"{app['name']} {title}",
        description=f"{app['name']} 계정·로컬·Apple·외부 데이터 삭제 경계",
        body=body,
    )


def app_terms(app: dict[str, Any], content: dict[str, Any]) -> tuple[str, str] | None:
    if not app.get("terms"):
        return None
    current_file = f"{app['slug']}/terms/index.html"
    sections = []
    for section in app["terms"]:
        section_html = f"<h2>{escape(section['title'])}</h2>"
        section_html += "".join(f"<p>{escape(value)}</p>" for value in section.get("paragraphs", []))
        if section.get("items"):
            section_html += list_html(section["items"])
        sections.append(section_html)
    body = f"""<article class="doc">
{heading(app, '이용약관', 'Terms')}
<p class="summary"><strong>요약:</strong> {escape(app.get('terms_summary', f"{app['name']} 이용 조건과 데이터 처리 경계를 설명합니다."))}</p>
{notice_html(app)}
{metadata_rows(app, content)}
{''.join(sections)}
{nav_html(current_file, app, include_terms=True)}
<footer>{escape(content['operator'])} · <a href="mailto:{escape(content['contact'])}">{escape(content['contact'])}</a> · 시행일 {escape(effective_date(app, content))}</footer>
</article>"""
    return current_file, page(
        current_file=current_file,
        title=f"{app['name']} 이용약관",
        description=f"{app['name']} 내부 베타 이용 조건",
        body=body,
    )


def alias_page(alias: str, app: dict[str, Any], route: str) -> tuple[str, str]:
    suffix = f"/{route}" if route else ""
    current_file = f"{alias}{suffix}/index.html"
    target_directory = f"{app['slug']}{suffix}"
    target = relative_href(current_file, target_directory)
    label = {
        "": "앱 안내",
        "privacy": "개인정보처리방침",
        "support": "지원",
        "delete-account": "계정 및 데이터 삭제",
        "data-deletion": "데이터 삭제 안내",
        "terms": "이용약관",
    }[route]
    head_extra = (
        f'<link rel="canonical" href="{escape(target)}" />\n'
        f'    <meta http-equiv="refresh" content="0; url={escape(target)}" />'
    )
    body = f"""<article class="doc compact">
<p class="eyebrow">이전 주소</p>
<h1>{escape(app['name'])}</h1>
<p>이 주소는 {escape(app['name'])} {escape(label)}의 별칭입니다.</p>
<p><a class="button-link" href="{escape(target)}">현재 문서로 이동</a></p>
</article>"""
    return current_file, page(
        current_file=current_file,
        title=f"{app['name']} {label}로 이동",
        description=f"{app['name']} 현재 정책 주소 안내",
        body=body,
        robots="noindex, follow",
        head_extra=head_extra,
    )


def root_page(content: dict[str, Any]) -> tuple[str, str]:
    current_file = "index.html"
    cards = []
    for app in content["apps"]:
        cards.append(
            f"""<a class="product-card" href="{escape(relative_href(current_file, app['slug']))}">
<strong>{escape(app['name'])}</strong>
<span>{escape(app['tagline'])}</span>
<code>{escape(app['bundle_id'])}</code>
</a>"""
        )
    body = f"""<article class="doc">
<p class="eyebrow">tedyway · Public policies</p>
<h1>앱 정책과 지원</h1>
<p class="lead">앱마다 실제 데이터 흐름과 삭제 경계가 다릅니다.</p>
<p>{escape(content['operator'])}가 운영하는 앱의 개인정보처리방침, 지원과 데이터 삭제 안내를 앱별로 제공합니다. 공통 문구로 실제 차이를 숨기지 않습니다.</p>
<div class="product-grid">{''.join(cards)}</div>
<nav class="nav">
  <a href="{escape(relative_href(current_file, 'support'))}">공통 지원 안내</a>
  <a href="{escape(relative_href(current_file, 'legal/privacy'))}">정책 목록</a>
  <a href="{escape(relative_href(current_file, 'legal/terms'))}">약관 목록</a>
</nav>
<footer>{escape(content['operator'])} · <a href="mailto:{escape(content['contact'])}">{escape(content['contact'])}</a> · 기준일 {escape(content['effective_date'])}</footer>
</article>"""
    return current_file, page(
        current_file=current_file,
        title=content["site_title"],
        description="tedyway 앱별 개인정보처리방침, 지원과 데이터 삭제 안내",
        body=body,
    )


def shared_support(content: dict[str, Any]) -> tuple[str, str]:
    current_file = "support/index.html"
    links = "".join(
        f'<li><a href="{escape(relative_href(current_file, app["slug"] + "/support"))}">{escape(app["name"])} 지원</a></li>'
        for app in content["apps"]
    )
    body = f"""<article class="doc">
<p class="eyebrow">tedyway · Support</p>
<h1>지원 안내</h1>
<p>모니터링하는 지원 채널은 <a href="mailto:{escape(content['contact'])}">{escape(content['contact'])}</a> 하나입니다.</p>
<p>앱별로 데이터와 권한이 다르므로 아래 앱 지원 페이지를 먼저 확인하세요.</p>
<ul>{links}</ul>
<h2>메일에 넣지 말아야 할 정보</h2>
<p>비밀번호, PAT·API 키, 인증 토큰, 세션 쿠키, 결제 정보, 정확한 위치, 아동 사진·영상과 업무 원문은 보내지 마세요.</p>
<p><a href="{escape(relative_href(current_file, ''))}">전체 앱으로 돌아가기</a></p>
<footer>{escape(content['operator'])} · 시행일 {escape(content['effective_date'])}</footer>
</article>"""
    return current_file, page(
        current_file=current_file,
        title="tedyway 앱 지원",
        description="tedyway 앱별 사용자 지원 안내",
        body=body,
    )


def shared_legal(content: dict[str, Any], terms: bool) -> tuple[str, str]:
    route = "legal/terms/index.html" if terms else "legal/privacy/index.html"
    title = "이용약관 목록" if terms else "개인정보처리방침 목록"
    items = []
    for app in content["apps"]:
        if terms and not app.get("terms"):
            continue
        suffix = "/terms" if terms else "/privacy"
        items.append(
            f'<li><a href="{escape(relative_href(route, app["slug"] + suffix))}">{escape(app["name"])} {escape("이용약관" if terms else "개인정보처리방침")}</a> <code>{escape(app["bundle_id"])}</code></li>'
        )
    note = (
        "앱별 이용약관이 있는 경우 이 목록에서 공개합니다. 각 앱이 연결하는 제3자 서비스의 약관과 Apple 조건도 별도로 적용될 수 있습니다."
        if terms
        else "앱별 데이터 흐름이 달라 하나의 포괄 방침으로 대체하지 않습니다. App Store의 Privacy Policy URL은 해당 앱 문서에 연결해야 합니다."
    )
    body = f"""<article class="doc">
<p class="eyebrow">tedyway · Legal index</p>
<h1>{escape(title)}</h1>
<p>{escape(note)}</p>
<ul>{''.join(items)}</ul>
<p><a href="{escape(relative_href(route, ''))}">전체 앱으로 돌아가기</a></p>
<footer>{escape(content['operator'])} · <a href="mailto:{escape(content['contact'])}">{escape(content['contact'])}</a> · 기준일 {escape(content['effective_date'])}</footer>
</article>"""
    return route, page(
        current_file=route,
        title=f"tedyway {title}",
        description=f"tedyway 앱별 {title}",
        body=body,
    )


def expected_files(content: dict[str, Any]) -> dict[str, str]:
    generated: dict[str, str] = {}
    for path, value in [root_page(content), shared_support(content), shared_legal(content, False), shared_legal(content, True)]:
        generated[path] = value

    for app in content["apps"]:
        pages = [
            app_landing(app, content),
            app_privacy(app, content),
            app_support(app, content),
            app_deletion(app, content),
        ]
        terms = app_terms(app, content)
        if terms:
            pages.append(terms)
        for path, value in pages:
            generated[path] = value

        routes = ["", "privacy", "support", deletion_route(app)]
        if app.get("terms"):
            routes.append("terms")
        for alias in app["aliases"]:
            for route in routes:
                path, value = alias_page(alias, app, route)
                generated[path] = value

    return generated


def write_files(files: dict[str, str]) -> None:
    for existing in SITE_ROOT.rglob("*.html"):
        existing.unlink()
    for relative_path, value in files.items():
        path = SITE_ROOT / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")


def check_files(files: dict[str, str]) -> int:
    failures: list[str] = []
    actual_paths = {
        path.relative_to(SITE_ROOT).as_posix()
        for path in SITE_ROOT.rglob("*.html")
    }
    expected_paths = set(files)
    for missing in sorted(expected_paths - actual_paths):
        failures.append(f"missing generated file: site/{missing}")
    for unexpected in sorted(actual_paths - expected_paths):
        failures.append(f"unexpected HTML file: site/{unexpected}")
    for relative_path in sorted(expected_paths & actual_paths):
        actual = (SITE_ROOT / relative_path).read_text(encoding="utf-8")
        if actual != files[relative_path]:
            failures.append(f"generated file is stale: site/{relative_path}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        print("run: make generate", file=sys.stderr)
        return 1
    print(f"generated site is current ({len(files)} HTML files)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated HTML is stale")
    args = parser.parse_args()

    content = load_content()
    files = expected_files(content)
    if args.check:
        return check_files(files)
    write_files(files)
    print(f"generated {len(files)} HTML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
