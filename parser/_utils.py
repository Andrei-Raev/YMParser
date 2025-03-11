def clean_url(url: str) -> str:
    return url.split('?', maxsplit=1)[0]
