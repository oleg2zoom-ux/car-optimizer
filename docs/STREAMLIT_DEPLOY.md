# העלאה ל-Streamlit Community Cloud

## שלב 1 — פתיחת GitHub repository

1. נכנסים ל-GitHub.
2. לוחצים New repository.
3. שם מומלץ: `car-optimizer`.
4. בוחרים Public.
5. יוצרים את ה-repository.

## שלב 2 — העלאת הקבצים

1. פותחים את קובץ ה-ZIP במחשב.
2. נכנסים ל-repository.
3. לוחצים Add file.
4. בוחרים Upload files.
5. גוררים את כל הקבצים והתיקיות:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `README_EN.md`
   - `.gitignore`
   - `.streamlit/`
   - `car_optimizer/`
   - `data/`
   - `docs/`
   - `scripts/`
6. לוחצים Commit changes.

## שלב 3 — יצירת אפליקציה ב-Streamlit

1. נכנסים ל-Streamlit Community Cloud.
2. לוחצים Create app.
3. בוחרים Deploy from GitHub repo.
4. בוחרים את ה-repository.
5. Branch: `main`
6. Main file path:

```text
app.py
```

7. לוחצים Deploy.

## תקלות נפוצות

אם מופיעה שגיאה על ספריות חסרות — לבדוק ש-`requirements.txt` עלה ל-GitHub.

אם מופיעה שגיאה שקובץ הנתונים לא נמצא — לבדוק שהתיקייה `data` והקובץ `sample_cars.csv` עלו.

אם העברית נראית מוזרה — לרוב זו בעיית דפדפן/כיווניות. האפליקציה כוללת CSS בסיסי לימין-לשמאל.
