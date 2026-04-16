SENSITIVE_PATTERNS = (
    "政治",
    "政府",
    "国家",
    "政党",
    "政策",
    "法律",
    "法规",
    "宪法",
    "制度",
    "体制",
    "敏感",
    "禁止",
    "违法",
    "违规",
    "非法",
    "抗议",
    "示威",
    "游行",
    "罢工",
    "暴动",
)


def normalize_text(text: object) -> str:
    """Normalize text input to UTF-8 safe string."""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    return text.encode("utf-8", errors="ignore").decode("utf-8")


def check_safety(text: object) -> bool:
    """Check whether input text passes simple safety filters."""
    try:
        normalized = normalize_text(text).lower()
        if not normalized:
            return True
        return not any(pattern in normalized for pattern in SENSITIVE_PATTERNS)
    except Exception as exc:
        print(f"检查安全性时发生错误: {exc}")
        return False
