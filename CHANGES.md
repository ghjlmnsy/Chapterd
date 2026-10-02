# Changes

## Book suggestions while typing (Open Library)

When adding or updating a book, typing at least 3 letters in **Title** shows matching books in a dropdown. Clicking one fills in the title, author and genre automatically. Without internet, no suggestions appear and everything else still works.

### New files

| File | Why it's there |
|---|---|
| `features/books/lookup.py` | Talks to Open Library: builds the search link and turns the reply into a clean list of title, author and genre. Kept separate from the screen code so each file has one job. |

### Changes

| What | How it works | File |
|---|---|---|
| Suggestions under the Title box | New `TitleSuggestions` class. It waits until you pause typing (0.4 s) so it doesn't search on every key, downloads in the background so the app never freezes, and ignores answers to older searches. | `features/books/widgets.py` |
| Genre is filled in automatically | Open Library lists many "subjects" per book. The genre mentioned most often among them (e.g. Fantasy, Mystery, Romance) is used, or "Fiction" if none match. | `features/books/lookup.py` |

---

## Rating fix, status colors and code cleanup

### New files

| File | Why it's there |
|---|---|
| `features/books/widgets.py` | The reusable book building blocks (book table, book form, status dropdown, star helper, status colors), moved out of `view.py`. `view.py` was getting crowded; now it only holds the book screen itself (341 → 210 lines). |

### Fixes and improvements

| # | What was wrong | What changed | File |
|---|---|---|---|
| 1 | The Rating box didn't respond to typing. | Rating is now a dropdown of stars ("Unrated", "★☆☆☆☆" … "★★★★★"). It still saves 0–5, so existing books are unaffected. | `features/books/widgets.py` |
| 2 | The small bar beside the selected option in the Status dropdown was always green. | The bar now matches the status: blue (Want to Read), amber (Reading), green (Finished), red (Dropped). Colors are in `STATUS_COLORS`. | `features/books/widgets.py` |
| 3 | The account rules (min/max lengths) were typed in three places, which could go out of sync. | They live only in `features/authentication/service.py`. The register form hints read them from there, and the database no longer keeps its own copy. | `features/authentication/service.py`, `features/authentication/view.py`, `database/database.py` |
| 4 | Leftover code: `get_book()` was never used, and `QHBoxLayout` was imported for nothing. | Both removed. | `database/database.py`, `features/books/view.py` |
| 5 | The list of reading statuses (`STATUSES`) lived in the database file, though it's a book rule. | Moved to `features/books/service.py`. `main.py` passes it to `database.create_tables(STATUSES)`, so the database's status check always follows this one list. | `features/books/service.py`, `database/database.py`, `main.py`, `tests/test_app.py` |

---

## Bug fixes and cleanup

### New files

| File | Why it's there |
|---|---|
| `.gitignore` | Stops Git from tracking files that shouldn't be shared: the database (`*.db`, holds accounts and password hashes) and Python cache (`__pycache__/`, rebuilt automatically). |
| `CHANGES.md` | A record of what changed and why. |


### Files removed from Git (still on your computer)

| File | Why |
|---|---|
| `chapterd.db` | Personal data (accounts and books). Each person gets their own database when they run the app. **Note:** the file still exists in older commits, so anyone with the repo history can still see it. |
| `__pycache__/*.pyc` | Python cache files that are generated automatically and differ per computer. |

### Fixes

| # | Problem | Fix | File |
|---|---|---|---|
| 1 | Database connections were never closed (only committed), so they built up and could lock the `.db` file on Windows. | `connect()` now always closes the connection when done. | `database/database.py` |
| 2 | An author name with `<` or `&` could break the Summary Stats page. | Text is escaped before it's shown. | `features/books/view.py` |
| 3 | Update tab: old text stayed in the form after switching tabs, and clicking another row silently threw away edits. | Form clears on refresh. Picking another row with unsaved edits asks "Discard your unsaved changes?" first. A "Changes saved!" message shows after saving. | `features/books/view.py` |
| 4 | Typing `%` or `_` in search matched every book. | These characters are now searched for literally. | `database/database.py` |
| 5 | A rating of 0 ("unrated") showed as `☆☆☆☆☆` / "0 / 5". | Shows "Unrated" in the table and in the rating box. | `features/books/view.py` |
| 6 | Stats said "(1 books)". | Says "1 book" / "2 books". | `features/books/view.py` |
| 7 | Pressing Enter in the Username box did nothing; the password stayed filled after a failed login. | Enter in any login or register field submits. The password clears after a failed login. | `features/authentication/view.py` |
| 8 | The main window had no minimize or maximize buttons. | Normal window buttons added. | `main.py` |
| 9 | "Jo" and "jo" could be two different accounts. | Usernames are case-insensitive for both register and login. The welcome message uses the name as it was registered. | `database/database.py`, `features/authentication/service.py` |
| 10 | "Most-logged author" counted "J.K. Rowling" and "j.k. rowling" separately. | Authors are grouped ignoring case. | `database/database.py` |
| 11 | The same book could be added twice. | Adding (or renaming to) a title + author already in your log shows an error. | `database/database.py`, `features/books/service.py` |
| 12 | The README was empty. | Added setup, run, test and layout instructions. | `README.md` |
| 13 | Minimum password was 4 characters. | Now 8 for **new** accounts (existing accounts still log in). | `features/authentication/service.py`, `database/database.py` |
| 14 | The database accepted any status or rating; no length limits. | The database now rejects invalid statuses and ratings. Usernames are limited to 30 characters, title/author/genre to 200 and notes to 2000. | `database/database.py`, `features/books/service.py`, `features/books/view.py`, `features/authentication/*` |

