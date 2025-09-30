# راهنمای فونت برای Onix

## فونت‌های پشتیبانی شده

برنامه Onix از فونت‌های زیر پشتیبانی می‌کند:

### فونت‌های فارسی/عربی

1. **Vazirmatn** (پیشنهادی) - فونت مدرن و خوانا
2. **Tahoma** - فونت پیش‌فرض ویندوز
3. **Arial** - فونت استاندارد
4. **Segoe UI** - فونت مدرن مایکروسافت

### فونت‌های انگلیسی

1. **Inter** - فونت مدرن و زیبا
2. **Segoe UI** - فونت پیش‌فرض ویندوز
3. **SF Pro Display** - فونت اپل
4. **system-ui** - فونت سیستم

## نحوه اضافه کردن فونت سفارشی

### 1. قرار دادن فایل فونت

```
onix/
├── fonts/
│   ├── your-font.ttf
│   ├── your-font.otf
│   └── your-font.woff2
```

### 2. فرمت‌های پشتیبانی شده

- **TTF** (TrueType Font) - `.ttf`
- **OTF** (OpenType Font) - `.otf`
- **WOFF2** (Web Open Font Format) - `.woff2`

### 3. تغییر فونت در کد

#### در `ui/styles.py`

```python
# خط 44 و 462 را تغییر دهید:
font-family: "Your-Font-Name", "Vazirmatn", "Tahoma", "Inter", "Segoe UI", "SF Pro Display", system-ui, sans-serif;
```

#### در `main.py` و `ui/main_window.py`

```python
# در استایل‌های RTL اضافه کنید:
app.setStyleSheet("""
    QWidget {
        font-family: "Your-Font-Name", "Vazirmatn", "Tahoma", "Inter", "Segoe UI", "SF Pro Display", system-ui, sans-serif;
        direction: rtl;
    }
""")
```

## فونت‌های پیشنهادی برای فارسی

### 1. Vazirmatn (پیشنهادی)

- **دانلود**: <https://github.com/rastikerdar/vazirmatn>
- **ویژگی‌ها**: مدرن، خوانا، پشتیبانی کامل از فارسی
- **فرمت**: TTF, OTF, WOFF2

### 2. IRANSans

- **دانلود**: <https://github.com/rastikerdar/iransans>
- **ویژگی‌ها**: فونت رسمی ایران، خوانا
- **فرمت**: TTF, OTF

### 3. Samim

- **دانلود**: <https://github.com/rastikerdar/samim>
- **ویژگی‌ها**: فونت محبوب، زیبا
- **فرمت**: TTF, OTF

## نحوه نصب فونت

### روش 1: نصب سیستم‌عامل

1. فایل فونت را دانلود کنید
2. روی فایل دوبار کلیک کنید
3. روی "نصب" کلیک کنید
4. برنامه را راه‌اندازی مجدد کنید

### روش 2: قرار دادن در پوشه fonts

1. پوشه `fonts` در ریشه پروژه ایجاد کنید
2. فایل فونت را در آن قرار دهید
3. نام فونت را در کد اضافه کنید

## تنظیمات پیشرفته

### تغییر اندازه فونت

```python
font-size: 16px;  # اندازه فونت
font-weight: 500; # وزن فونت (100-900)
```

### تنظیمات RTL

```python
direction: rtl;           # جهت راست به چپ
text-align: right;        # تراز متن به راست
padding-right: 8px;       # فاصله از راست
padding-left: 0px;        # فاصله از چپ
```

## عیب‌یابی

### اگر فونت نمایش داده نمی‌شود

1. نام فونت را بررسی کنید
2. فایل فونت را در مسیر صحیح قرار دهید
3. برنامه را راه‌اندازی مجدد کنید
4. از فونت‌های پشتیبانی شده استفاده کنید

### اگر فونت در RTL درست نمایش داده نمی‌شود

1. `direction: rtl` را اضافه کنید
2. `text-align: right` را تنظیم کنید
3. padding و margin را برای RTL تنظیم کنید
