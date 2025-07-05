# SD Copier

**SD Copier** is a modern, user-friendly tool for quickly copying photos, videos, and sound files from multiple SD cards to your computer. It supports parallel transfers, customizable destination folders, automatic file renaming to avoid overwrites, and a clear, emoji-enhanced graphical interface.

---

## Features

- **Automatic SD Card Detection:** Detects all removable SD cards as soon as they are inserted.
- **Parallel Transfers:** Copy from multiple SD cards at the same time for maximum speed.
- **Customizable Folders:** Set your own main, pictures, videos, and sound folders.
- **Dated & Subfolders:** Easily create folders for today’s date or use special subfolders like "Azza" or "Reading".
- **Automatic File Renaming:** Files are renamed with date and hour suffixes to prevent overwriting.
- **Transfer Progress:** See real-time progress and speed for each SD card.
- **Automatic Eject:** SD cards are safely ejected after transfer.
- **Modern GUI:** Clean, emoji-enhanced interface for ease of use.

---

## How to Use

### 1. Run the App

- **Option 1 (Recommended for Windows):**  
  Run the ready-to-use portable version:  
  `dist/main.exe`

- **Option 2:**  
  Run with Python:  
  ```sh
  python main.py
  ```

### 2. Select Folders

- Optionally set the main folder, or use the default.
- You can also set custom Pictures, Videos, and Sound folders.

### 3. Create Dated or Subfolder

- Use the **"Create Today's Folder"** button for a dated folder.
- Use the **Azza/Reading** buttons to create/use a subfolder.

### 4. Insert SD Cards

- The app will list all detected SD cards. Select which ones to copy.

### 5. Start Transfer

- Click **"Start Transfer"** to begin copying. Progress and speed are shown for each card.

### 6. Eject and Done

- SD cards are ejected automatically after transfer.
- Use the **"Open"** button to open the main folder in Explorer.

---

## Making it Portable

You can use [PyInstaller](https://www.pyinstaller.org/) to create a standalone `.exe`:

```sh
pyinstaller --onefile --noconsole --add-data "assets\\logo.jpg;assets" main.py
```

The output will be in the `dist` folder. Copy and run on any Windows PC.

---

## Requirements

- Windows 10/11
- Python 3.8+ (if not using the portable `.exe`)
- Standard Windows tools (PowerShell, WMIC)

---

## License

MIT License

---

**Enjoy fast, safe, and organized transfers with SD Copier!**

---

**Developed By S.Khadeeja Dev Team**

---

# SD Copier (بالعربية)

**SD Copier** هو أداة حديثة وسهلة الاستخدام لنسخ الصور والفيديوهات وملفات الصوت بسرعة من عدة بطاقات SD إلى جهاز الكمبيوتر الخاص بك. يدعم النقل المتوازي، وتخصيص مجلدات الوجهة، وإعادة تسمية الملفات تلقائيًا لتجنب الاستبدال، وواجهة رسومية حديثة مدعمة بالرموز التعبيرية.

---

## الميزات

- **الكشف التلقائي عن بطاقات SD:** يكتشف جميع بطاقات SD القابلة للإزالة بمجرد إدخالها.
- **النقل المتوازي:** انسخ من عدة بطاقات SD في نفس الوقت لتحقيق أقصى سرعة.
- **مجلدات قابلة للتخصيص:** يمكنك تعيين المجلد الرئيسي ومجلدات الصور والفيديو والصوت حسب رغبتك.
- **مجلدات مؤرخة وفرعية:** أنشئ بسهولة مجلدات بتاريخ اليوم أو استخدم مجلدات فرعية مثل "عزة" أو "قراءة".
- **إعادة تسمية الملفات تلقائيًا:** تتم إعادة تسمية الملفات بإضافة التاريخ والساعة لمنع الاستبدال.
- **عرض تقدم النقل:** شاهد تقدم النقل وسرعته لكل بطاقة SD في الوقت الفعلي.
- **إخراج تلقائي:** يتم إخراج بطاقات SD بأمان بعد انتهاء النقل.
- **واجهة رسومية حديثة:** واجهة نظيفة وسهلة الاستخدام مع رموز تعبيرية.

---

## كيفية الاستخدام

### 1. تشغيل التطبيق

- **الخيار 1 (موصى به لويندوز):**  
  شغّل النسخة المحمولة الجاهزة:  
  `dist/main.exe`

- **الخيار 2:**  
  شغّل باستخدام بايثون:  
  ```sh
  python main.py
  ```

### 2. اختيار المجلدات

- يمكنك تعيين المجلد الرئيسي أو استخدام الافتراضي.
- يمكنك أيضًا تعيين مجلدات الصور والفيديو والصوت حسب رغبتك.

### 3. إنشاء مجلد بتاريخ اليوم أو مجلد فرعي

- استخدم زر **"إنشاء مجلد اليوم"** لإنشاء مجلد بتاريخ اليوم.
- استخدم أزرار **عزة/قراءة** لإنشاء أو استخدام مجلد فرعي.

### 4. إدخال بطاقات SD

- سيعرض التطبيق جميع بطاقات SD المكتشفة. اختر البطاقات التي تريد نسخها.

### 5. بدء النقل

- اضغط على **"بدء النقل"** لبدء النسخ. سيتم عرض التقدم والسرعة لكل بطاقة.

### 6. الإخراج والانتهاء

- يتم إخراج بطاقات SD تلقائيًا بعد انتهاء النقل.
- استخدم زر **"فتح"** لفتح المجلد الرئيسي في مستكشف الملفات.

---

## جعل التطبيق محمولاً

يمكنك استخدام [PyInstaller](https://www.pyinstaller.org/) لإنشاء ملف تنفيذي مستقل:

```sh
pyinstaller --onefile --noconsole main.py
```

سيكون الناتج في مجلد `dist`. يمكنك نسخه وتشغيله على أي جهاز ويندوز.

---

## المتطلبات

- ويندوز 10 أو 11
- بايثون 3.8 أو أحدث (إذا لم تستخدم النسخة المحمولة)
- أدوات ويندوز القياسية (PowerShell, WMIC)

---

## الرخصة

رخصة MIT

---

**استمتع بنقل سريع وآمن ومنظم مع SD Copier!**

---

**تم التطوير بواسطة فريق S.Khadeeja Dev Team**