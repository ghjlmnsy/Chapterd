# Changes

## 2026-10-02 — Bug fixes and cleanup

### New files

| File | Why it's there |
|---|---|
| `.gitignore` | Stops Git from tracking files that shouldn't be shared: the database (`*.db`, holds accounts and password hashes) and Python cache (`__pycache__/`, rebuilt automatically). |
| `CHANGES.md` | This file. A record of what changed and why. |
| `letterbook_pyqt/chapterd_qt/tests/test_app.py` | Automated tests for accounts, books, search and stats. Run with `python -m unittest discover -s tests -v` from the `chapterd_qt` folder. |

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
| 9 | "Ann" and "ann" could be two different accounts. | Usernames are case-insensitive for both register and login. The welcome message uses the name as it was registered. | `database/database.py`, `features/authentication/service.py` |
| 10 | "Most-logged author" counted "J.K. Rowling" and "j.k. rowling" separately. | Authors are grouped ignoring case. | `database/database.py` |
| 11 | The same book could be added twice. | Adding (or renaming to) a title + author already in your log shows an error. | `database/database.py`, `features/books/service.py` |
| 12 | Popups said "LetterBook" while the app is called "Chapterd". | Popups and the window class (`ChapterdWindow`) now say Chapterd. | `features/books/view.py`, `main.py` |
| 13 | The README was empty. | Added setup, run, test and layout instructions. | `README.md` |
| 14 | Minimum password was 4 characters. | Now 8 for **new** accounts (existing accounts still log in). | `features/authentication/service.py`, `database/database.py` |
| 15 | The database accepted any status or rating; no length limits. | The database now rejects invalid statuses and ratings. Usernames are limited to 30 characters, title/author/genre to 200 and notes to 2000. | `database/database.py`, `features/books/service.py`, `features/books/view.py`, `features/authentication/*` |
| 16 | No tests. | Added `tests/test_app.py` (11 tests). | `tests/test_app.py` |

### Database upgrade

Existing `chapterd.db` files upgrade automatically the next time the app starts. No data is lost. The upgrade adds a case-insensitive username index and two validation triggers.

### Not changed

- The folder name `letterbook_pyqt` still uses the old name. Renaming it would move every file, so that's left for you to decide.
