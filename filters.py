"""카테고리 제외 규칙.

FILTER_ENABLED = False 이면 사용자가 추가한 제외 규칙을 모두 끈다.
(메뉴 UI용 '더보기' 항목만 계속 제외)
"""
from __future__ import annotations

# False → 아래 KC/어린이/식품/다이소 등 제외 규칙 전부 해제
FILTER_ENABLED = False

# ── 통째로 제외할 대분류(L1) ────────────────────────────────
EXCLUDED_L1 = {
    "출산/유아동",
    "가전디지털",
    "식품",
    "뷰티",
    "도서/음반/DVD",
}

# ── 특정 중분류(L2)만 제외 ──────────────────────────────
EXCLUDED_L2 = {
    "비타민/미네랄",
    "건강식품",
    "허브/식물추출물",
    "홍삼/인삼",
    "건강즙/음료",
    "꿀/프로폴리스",
    "건강분말/건강환",
    "헬스보충식품",
    "다이어트/이너뷰티",
    "영양식/선식",
    "어린이 건강식품",
    "건강도서",
}

CHILDREN_KEYWORDS = [
    "유아", "아동", "어린이", "베이비", "주니어", "키즈", "신생아",
    "출산", "기저귀", "분유", "이유식", "유아동", "임부", "산모",
    "완구", "장난감", "보행기", "유모차", "카시트", "젖병",
]

KC_KEYWORDS = [
    "가전", "전자", "전기", "충전", "충전식", "배터리", "보조배터리",
    "건전지", "콘센트", "멀티탭", "어댑터", "전선", "전원", "발열",
    "조명", "램프", "전구", "led", "led등", "형광등", "스탠드",
    "노트북", "컴퓨터", "데스크탑", "모니터", "프린터", "스캐너",
    "마우스", "키보드", "공유기", "ssd", "hdd", "메모리카드",
    "휴대폰", "스마트폰", "태블릿", "스마트워치", "이어폰", "헤드폰",
    "헤드셋", "스피커", "tv", "텔레비전", "카메라", "캠코더", "드론",
    "게임기", "콘솔", "프로젝터", "마이크",
    "전동", "안마", "마사지", "면도기", "드라이어", "드라이기", "고데기",
    "청소기", "세탁기", "건조기", "냉장고", "에어컨", "선풍기", "써큘레이터",
    "히터", "난로", "온풍기", "전기장판", "전기매트", "온수매트", "전기요",
    "인덕션", "전기레인지", "전자레인지", "오븐", "에어프라이어", "밥솥",
    "믹서", "블렌더", "토스터", "커피머신", "전기포트", "정수기",
    "가습기", "제습기", "공기청정기", "비데", "전기면도", "전기칫솔",
]

OTHER_KEYWORDS = [
    "성인용품",
    "화장품",
    "사료",
    "영양제",
    "간식",
    "보충식",
    "처방식",
]

DAISO_BRANCH = [
    "생활잡화", "주방잡화", "주방수납/잡화", "욕실용품/잡화",
    "일회용", "파티/이벤트", "데코/포장용품",
]
DAISO_NAME = [
    "메모지", "포스트잇", "점착메모", "수첩",
    "데코테이프", "마스킹테이프", "생활테이프", "네임스티커", "스탬프",
    "반짇고리",
    "수세미", "행주", "고무장갑", "냅킨", "키친타올",
    "조화",
    "정리소품", "수납케이스", "정리함", "데스크정리",
    "캔들", "디퓨저", "방향제",
]


def _norm(s: str) -> str:
    return (s or "").lower()


def exclusion_reason(category: dict) -> str | None:
    """제외 사유 문자열을 돌려준다. 제외 대상이 아니면 None."""
    name = category.get("name", "")
    if name in {"더보기", ""}:
        return "유효하지 않은 항목(더보기 등)"

    if not FILTER_ENABLED:
        return None

    l1 = category.get("l1", "")
    if l1 in EXCLUDED_L1:
        return f"대분류 제외({l1})"

    path = category.get("path", [category.get("name", "")])
    if len(path) >= 2 and path[1] in EXCLUDED_L2:
        return f"중분류 제외({path[1]})"

    haystack = _norm(" > ".join(path))

    for kw in CHILDREN_KEYWORDS:
        if _norm(kw) in haystack:
            return f"어린이/유아 제품 키워드('{kw}')"

    for kw in KC_KEYWORDS:
        if _norm(kw) in haystack:
            return f"KC 인증 대상 키워드('{kw}')"

    for kw in OTHER_KEYWORDS:
        if _norm(kw) in haystack:
            return f"기타 제외 키워드('{kw}')"

    for kw in DAISO_BRANCH:
        if _norm(kw) in haystack:
            return f"다이소형 제외(분류 '{kw}')"

    leaf = _norm(name)
    for kw in DAISO_NAME:
        if _norm(kw) in leaf:
            return f"다이소형 제외('{kw}')"

    return None


def is_allowed(category: dict) -> bool:
    return exclusion_reason(category) is None
