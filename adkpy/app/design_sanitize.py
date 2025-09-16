"""
Lightweight sanitization and validation for HTML/CSS/SVG design payloads.

This module intentionally avoids heavy dependencies and applies conservative
regex-based checks. It is not a full sanitizer, but it blocks common hazards
and trims disallowed constructs to keep the API stable.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

# Whitelists
ALLOWED_TAGS = {
    'section','div','h1','h2','h3','p','ul','ol','li','span','strong','em','b','i',
    'svg','g','path','rect','circle','polygon','line','defs','linearGradient','stop'
}
ALLOWED_ATTRS = {
    'id','class','style','fill','stroke','stroke-width','stroke-linecap','stroke-linejoin','rx','ry','x','y','cx','cy','r','d','width','height','viewBox','preserveAspectRatio'
}
ALLOWED_CSS_PROPS = {
    'position','inset','top','right','bottom','left','display','grid-template-columns','grid-template-rows','gap','row-gap','column-gap','width','height','margin','margin-left','margin-right','margin-top','margin-bottom','padding','padding-left','padding-right','padding-top','padding-bottom','color','background','background-image','background-size','background-position','background-repeat','border-radius','font-family','font-weight','font-size','line-height','letter-spacing','text-align','align-items','justify-content','opacity','list-style','list-style-type','z-index','overflow','contain','isolation'
}

RE_SCRIPT = re.compile(r"<\s*/?\s*script[^>]*>", re.I)
RE_EVENT_ATTR = re.compile(r"on[a-z]+\s*=", re.I)
RE_URL_FUNC = re.compile(r"url\s*\(", re.I)
RE_IMPORT = re.compile(r"@import", re.I)

def _strip_disallowed_tags(html: str) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    # Remove script tags entirely
    if RE_SCRIPT.search(html or ''):
        warnings.append('Removed <script> tags')
        html = RE_SCRIPT.sub('', html)
    # Remove event handler attributes
    if RE_EVENT_ATTR.search(html or ''):
        warnings.append('Removed event handler attributes')
        html = RE_EVENT_ATTR.sub('x=', html)
    # Remove unknown tags using a very conservative approach: strip tags but keep text
    def _strip_unknown(m):
        tag = m.group(1).lower()
        if tag in ALLOWED_TAGS:
            return m.group(0)
        warnings.append(f'Removed tag <{tag}>')
        return ''
    html = re.sub(r"<\s*([a-zA-Z0-9:_-]+)([^>]*)>", _strip_unknown, html)
    return html, warnings

def _sanitize_style_attr(html: str) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    # Very naive style attr filter: keep only allowed properties; drop url() and @import
    def _clean_style(m):
        style = m.group(1)
        if RE_URL_FUNC.search(style) or RE_IMPORT.search(style):
            warnings.append('Stripped unsafe style url()/@import')
            return ''
        # Recompose allowed declarations
        decls = []
        for part in style.split(';'):
            kv = part.split(':', 1)
            if len(kv) != 2:
                continue
            prop = kv[0].strip().lower()
            val = kv[1].strip()
            if prop in ALLOWED_CSS_PROPS:
                decls.append(f"{prop}:{val}")
        if not decls:
            return ''
        return f" style=\"{';'.join(decls)}\""
    html2 = re.sub(r"\sstyle=\"([^\"]*)\"", _clean_style, html)
    return html2, warnings

def validate_html(html: str) -> Tuple[bool, List[str], List[str]]:
    if not html:
        return True, [], []
    errors: List[str] = []
    warnings: List[str] = []
    if RE_SCRIPT.search(html):
        errors.append('Contains <script> tags')
    if RE_EVENT_ATTR.search(html):
        errors.append('Contains event handler attributes')
    if '<iframe' in html.lower():
        errors.append('Contains <iframe> tag')
    return (len(errors) == 0), warnings, errors

def sanitize_html(html: str) -> Tuple[str, List[str]]:
    if not html:
        return html, []
    h, warnings1 = _strip_disallowed_tags(html)
    h2, warnings2 = _sanitize_style_attr(h)
    return h2, warnings1 + warnings2

def validate_css(css: str) -> Tuple[bool, List[str], List[str]]:
    if not css:
        return True, [], []
    errors: List[str] = []
    warnings: List[str] = []
    if RE_IMPORT.search(css) or RE_URL_FUNC.search(css):
        errors.append('CSS contains @import or url()')
    return (len(errors) == 0), warnings, errors

def sanitize_css(css: str) -> Tuple[str, List[str]]:
    if not css:
        return css, []
    warnings: List[str] = []
    # Drop @import and url()
    if RE_IMPORT.search(css) or RE_URL_FUNC.search(css):
        warnings.append('Removed @import/url() from CSS')
        css = RE_IMPORT.sub('', css)
        css = RE_URL_FUNC.sub('', css)
    return css, warnings

def validate_svg(svg: str) -> Tuple[bool, List[str], List[str]]:
    if not svg:
        return True, [], []
    errors: List[str] = []
    warnings: List[str] = []
    if RE_SCRIPT.search(svg) or RE_EVENT_ATTR.search(svg):
        errors.append('SVG contains script or event handlers')
    return (len(errors) == 0), warnings, errors

def sanitize_svg(svg: str) -> Tuple[str, List[str]]:
    if not svg:
        return svg, []
    s, warnings1 = _strip_disallowed_tags(svg)
    # remove forbidden attrs broadly
    s2 = re.sub(r"\son[a-zA-Z]+\s*=\s*\"[^\"]*\"", '', s)
    return s2, warnings1

