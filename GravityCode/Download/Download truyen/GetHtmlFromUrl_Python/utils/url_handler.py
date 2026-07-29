from urllib.parse import urlparse

def normalize_host(url: str) -> str:
    """Giả lập hàm normalizeHost trong utils.UrlHandler của Java"""
    if not url:
        return ""
    if "://" not in url:
        url = "http://" + url
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return url
