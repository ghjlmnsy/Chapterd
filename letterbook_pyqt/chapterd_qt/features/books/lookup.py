"""Book suggestions from Open Library (free, no API key): https://openlibrary.org/dev/docs/api/search"""
import json
from urllib.parse import urlencode

SEARCH_URL = "https://openlibrary.org/search.json"

# Open Library lists many "subjects" per book; the genre mentioned most often in them wins.
# Plain "Fiction" is only used when none of the others are mentioned.
GENRES = [
    "Fantasy", "Science fiction", "Horror", "Mystery", "Thriller", "Romance",
    "Historical fiction", "Young adult", "Poetry", "Biography", "Self-help",
    "History", "Philosophy",
]


def search_url(title, limit=8):
    """The Open Library search URL for a title."""
    query = {"title": title, "fields": "title,author_name,subject", "limit": limit}
    return f"{SEARCH_URL}?{urlencode(query)}"


def pick_genre(subjects):
    """Picks a simple genre from Open Library's subject list ("" if none fits)."""
    subjects = [subject.lower() for subject in subjects]
    counts = {genre: sum(genre.lower() in subject for subject in subjects) for genre in GENRES}
    best = max(GENRES, key=counts.get)
    if counts[best]:
        return best
    return "Fiction" if any("fiction" in subject for subject in subjects) else ""


def parse_results(data):
    """Turns Open Library's JSON reply into [{"title", "author", "genre"}], without duplicates."""
    books, seen = [], set()
    for doc in json.loads(data).get("docs", []):
        title = doc.get("title", "").strip()
        author = ", ".join(doc.get("author_name", [])[:2])  # at most 2 authors
        key = (title.lower(), author.lower())
        if title and key not in seen:
            seen.add(key)
            books.append({"title": title, "author": author, "genre": pick_genre(doc.get("subject", []))})
    return books
