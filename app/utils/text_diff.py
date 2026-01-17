from difflib import SequenceMatcher
from simhash import simhash
import re


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def simhash_similarity(a: str, b: str) -> float:
    ha = simhash(a.split())
    hb = simhash(b.split())
    hamming = bin(ha ^ hb).count("1")
    return 1 - (hamming / 64)


def extract_numbers(text: str):
    return re.findall(r"\d+(?:\.\d+)?", text)


def numeric_change(a: str, b: str) -> bool:
    na = extract_numbers(a)
    nb = extract_numbers(b)
    return na != nb


def token_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def should_update(old_text: str, new_text: str, min_similarity: float = 0.95) -> bool:
    """
    Returns True if the new text is different from the old text.
    Otherwise returns False.

    Args:
        old_text (str): The old text.
        new_text (str): The new text.
        min_similarity (float, optional): The minimum similarity threshold. Defaults to 0.95.

    Returns:
        bool: True if the new text is different from the old text, False otherwise.
    """
    if not old_text or not new_text:
        return old_text != new_text

    old = normalize(old_text)
    new = normalize(new_text)

    if numeric_change(old, new):
        return True  # small but important change

    simhash_sim = simhash_similarity(old, new)
    if simhash_sim > min_similarity:
        return False

    token_sim = token_similarity(old, new)

    return token_sim < min_similarity
