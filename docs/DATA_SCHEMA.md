# סכמה למסד נתוני רכבים

הקובץ המרכזי צריך להיות CSV או Excel עם עמודות קבועות. המחשבון קורא את הקובץ ומחשב על בסיסו תחזית שווי עתידי ועלות בעלות.

## עמודות חובה

`record_id`  
מזהה חד-חד ערכי לתצפית.

`manufacturer`  
יצרן, לדוגמה: Hyundai, Toyota, Chery.

`model`  
דגם, לדוגמה: Kona, Corolla, Tiggo 4.

`trim`  
רמת גימור, לדוגמה: Prestige, Luxury, Premium.

`model_year`  
שנתון הרכב.

`category`  
קטגוריית גודל או שימוש: סופר מיני, משפחתית קומפקטית, קרוסאובר קטן, קרוסאובר בינוני, 7 מקומות.

`powertrain`  
סוג הנעה: Gasoline, Diesel, Hybrid, PHEV, EV.

`ownership_type`  
סוג מקור/בעלות: New, Private Used, Leasing Used, Trade-in, Rental.

`km`  
קילומטראז׳ בתצפית.

`hand`  
מספר יד.

`purchase_price`  
המחיר שהמחשבון משתמש בו כעלות רכישה.

`annual_depr_rate`  
שיעור שחיקת מחיר שנתי משוער, בין 0 ל-1. לדוגמה 0.10 פירושו 10% לשנה.

`risk_sigma`  
סטיית סיכון יחסית סביב התחזית, בין 0 ל-1. לדוגמה 0.15 פירושו טווח סיכון של כ-15%.

`source_type`  
סוג מקור הנתון: Demo, Listing, Dealer, Trade-in, Pricebook, Reported Deal.

`source_confidence`  
רמת אמינות מקור בין 0 ל-1. מקור רשמי או עסקה בפועל יקבל ציון גבוה יותר ממודעת מחיר מבוקש.

## עמודות מומלצות

`observation_date`  
תאריך איסוף הנתון.

`source_name`  
שם האתר/חברה/מחירון.

`msrp_new`  
מחיר חדש רשמי או מחיר יבואן.

`asking_price`  
מחיר מבוקש במודעה.

`deal_price_est`  
מחיר עסקה משוער.

`trade_in_price_est`  
הערכת מחיר טרייד-אין.

`notes`  
הערות חופשיות.

## כלל חשוב

לא לערבב בין סוגי מחיר בלי לציין מקור. מחיר מודעה, מחיר טרייד-אין, מחיר מחירון ומחיר עסקה אמיתי אינם אותו דבר.
