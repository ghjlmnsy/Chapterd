# Chapterd

A desktop book log built with Python and PyQt6. Create an account, then add, search, update and remove the books you read and see a summary of your reading.

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

## Run the tests

```
cd letterbook_pyqt/chapterd_qt
python -m unittest discover -s tests -v
```

## Project layout

```
letterbook_pyqt/chapterd_qt/
├── main.py                      app entry point and main window
├── style.qss                    app colors and styling
├── requirements.txt             Python packages needed
├── database/database.py         all SQLite access (accounts and books)
├── features/authentication/     login and register (service = logic, view = screen)
├── features/books/              book log screens and rules
└── tests/test_app.py            automated tests
```

See [CHANGES.md](CHANGES.md) for the list of changes and new files.
