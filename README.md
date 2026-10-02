# Chapterd

A desktop book log built with Python and PyQt6. Create an account, then add, search, update and remove the books you read and see a summary of your reading.

When you type a title, the app suggests matching books from [Open Library](https://openlibrary.org) and fills in the author and genre for you. This needs an internet connection; everything else works offline.

## Requirements

- Python 3.10 or newer
- PyQt6 (installed in step 1 below)

## Run the app

```
cd letterbook_pyqt/chapterd_qt
python -m pip install -r requirements.txt
python main.py
```

The first run creates `chapterd.db` in the same folder. That file holds your accounts and books. It is local only and ignored by Git.

## Project layout

```
letterbook_pyqt/chapterd_qt/
├── main.py                      app entry point and main window
├── style.qss                    app colors and styling
├── requirements.txt             Python packages needed
├── database/database.py         all SQLite access (accounts and books)
├── features/authentication/     login and register (service = logic, view = screen)
└── features/books/              book log screens, rules and Open Library suggestions
```