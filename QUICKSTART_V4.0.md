# Quick Start Guide - Database Integration

## 🚀 How to Use V4.0

### Step 1: Install (if needed)

```bash
# No new dependencies! SQLite is built into Python
pip install --upgrade --no-cache-dir yfinance  # Only if you haven't already
```

---

### Step 2: Update Main App

**Option A: Minimal Change (Quick)**

In `alphatic_portfolio_app.py`, change:

```python
# OLD:
from sidebar_panel import render_sidebar

# NEW:
from sidebar_panel_db import render_sidebar
```

That's it! Everything else stays the same.

---

**Option B: Keep Both (Testing)**

```python
# Import both
from sidebar_panel import render_sidebar as render_sidebar_old
from sidebar_panel_db import render_sidebar as render_sidebar_new

# Add toggle in sidebar
use_database = st.sidebar.checkbox("Use Database (V4.0)", value=True)

if use_database:
    render_sidebar_new()
else:
    render_sidebar_old()
```

---

### Step 3: Run the App

```bash
streamlit run alphatic_portfolio_app.py
```

---

### Step 4: First Use

**Login:**
```
1. Enter username (any name, min 3 chars)
2. Click "Login / Create Account"
3. You're in!
```

**Create Portfolio:**
```
1. Enter tickers (e.g., SPY, QQQ, AGG)
2. Choose allocation method
3. Choose public/private
4. Click "Build & Save Portfolio"
5. Portfolio saved to database!
```

**Refresh Browser:**
```
1. Press F5 to refresh
2. Login again
3. Your portfolios are still there! ✅
```

---

## 📁 File Structure

```
Your Project/
├── alphatic_portfolio_app.py       # Main app (update import)
├── database.py                      # NEW - Database module
├── sidebar_panel_db.py              # NEW - DB sidebar
├── sidebar_panel.py                 # OLD - Keep for reference
├── helper_functions.py              # No changes
├── tabs/                            # No changes
│   ├── tab_01_overview.py
│   ├── tab_02_detailed_analysis.py
│   └── ...
└── portfolios.db                    # NEW - Auto-created on first run
```

---

## 🔧 Database Location

**Default:** `portfolios.db` in project root

**Custom location:**

```python
# In sidebar_panel_db.py or main app:
if 'db' not in st.session_state:
    st.session_state.db = PortfolioDB(db_path="path/to/your/portfolios.db")
```

---

## 💾 Backup Your Database

**SQLite database is a single file!**

```bash
# Backup:
cp portfolios.db portfolios_backup.db

# Restore:
cp portfolios_backup.db portfolios.db
```

**Or use SQLite tools:**
```bash
sqlite3 portfolios.db .dump > backup.sql
sqlite3 new_portfolios.db < backup.sql
```

---

## 🔍 Inspect Database (Optional)

**Using Python:**
```python
from database import PortfolioDB

db = PortfolioDB()

# List all users
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    print(users)

# List all portfolios
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT name, user_id, is_public FROM portfolios")
    portfolios = cursor.fetchall()
    print(portfolios)
```

**Using DB Browser:**
```
1. Download DB Browser for SQLite (free)
2. Open portfolios.db
3. Browse tables, run queries
```

---

## 🌍 Public Portfolio Discovery

**Browse Public Portfolios:**

After logging in, scroll down in sidebar to:
```
💾 Saved Portfolios
  
  Your Portfolios:
    [Your private/public portfolios]
  
  Public Portfolios:
    [Other users' public portfolios]
```

**Load Public Portfolio:**
```
1. Click "View" on public portfolio
2. Analyze it (read-only)
3. Cannot modify or delete
```

---

## 🔐 Security Notes

**Current (V4.0):**
- No passwords (username only)
- Simple authentication
- Good for personal use / small teams
- Not for production with sensitive data

**If You Need Security:**
- Wait for V5.0 (passwords, encryption)
- Or use authentication service (Auth0, Firebase)
- Or host behind VPN/private network

---

## ❓ FAQ

### Q: What if I forget my username?

**A:** Look in `portfolios.db`:
```python
from database import PortfolioDB
db = PortfolioDB()

with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    users = cursor.fetchall()
    print([u['username'] for u in users])
```

---

### Q: Can I migrate old portfolios?

**A:** Old portfolios weren't persistent, so nothing to migrate. Just rebuild them - they'll be cached for speed!

---

### Q: Can I have multiple databases?

**A:** Yes! Different database files for different environments:
```python
# Development
db_dev = PortfolioDB("portfolios_dev.db")

# Production
db_prod = PortfolioDB("portfolios_prod.db")
```

---

### Q: How do I clear all data?

**A:** Delete the database file:
```bash
rm portfolios.db
```
Next run will create a fresh database.

---

### Q: Can I export my portfolios?

**A:** Yes! Use SQLite dump:
```bash
sqlite3 portfolios.db .dump > my_portfolios.sql
```

Or write custom export:
```python
from database import PortfolioDB
import json

db = PortfolioDB()
portfolios = db.get_user_portfolios("your_user_id")

with open('portfolios.json', 'w') as f:
    json.dump(portfolios, f, indent=2, default=str)
```

---

## 🎯 Comparison: V3.8 vs V4.0

| Feature | V3.8 (Session State) | V4.0 (Database) |
|---------|---------------------|-----------------|
| **Persistence** | ❌ Lost on refresh | ✅ Permanent |
| **Multi-user** | ❌ Single session | ✅ Multiple users |
| **Sharing** | ❌ No sharing | ✅ Public/Private |
| **Authentication** | ❌ None | ✅ Username-based |
| **Backup** | ❌ Can't backup | ✅ Single file backup |
| **Scalability** | ❌ Session memory | ✅ SQLite (1TB+) |

---

## ✅ Checklist

Before deploying:

- [  ] Backup `portfolios.db` regularly
- [  ] Set appropriate file permissions
- [  ] Test login/logout flow
- [  ] Test portfolio save/load
- [  ] Test public/private toggle
- [  ] Test multi-user access
- [  ] Document usernames for your users

---

## 🚀 Ready to Go!

**V4.0 is ready for production use with:**
- ✅ Permanent storage
- ✅ Multi-user support
- ✅ Portfolio sharing
- ✅ Simple setup (1 file change)
- ✅ Zero new dependencies

**Just change the import and you're done!**
