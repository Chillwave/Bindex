 
# BinDex - Storage Bin Tracking System

**BinDex** is a lightweight Flask-based web application for managing and tracking physical storage bins. It features QR code generation, PDF label printing, TOTP + PIN authentication, and inventory tracking by container and rack location.

---

## Features

- ✅ Register/login using 4-digit PIN + TOTP (Google Authenticator-compatible)
- ✅ Secure session handling with 30-minute inactivity timeout
- ✅ Create new bins with prefix + location
- ✅ Auto-generate QR codes and printable 2-up PDF shipping labels
- ✅ Track items by bin with optional UPC barcode links
- ✅ Search for items across your assigned bins
- ✅ Delete items from bins
- ✅ Upload or select a visual icon per bin prefix
- ✅ Per-user bin isolation (users cannot see each other's bins)

---

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

---

## Running the App

```bash
python run.py
```

Then visit [http://localhost:5000](http://localhost:5000) in your browser.

To allow LAN access:

```bash
python run.py --host=0.0.0.0
```

---

## 👤 User Authentication

- Click "Generate Credentials" on the login page
- Scan the QR with Google Authenticator or similar
- Use the generated 4-digit PIN and current TOTP to log in

User data is stored in `app/users.json`.

---

## Data Storage

- Bin and item data is stored in `app/data.json`, organized per user
- Uploaded prefix images go in `app/static/prefix_images`
- QR codes for TOTP setup go in `app/static/qrcodes`
- Generated shipping labels are stored in `app/labels`

---

## Label Format

PDF labels are generated in 2-up layout on 8.5"x11" for standard half-sheet shipping labels.

---

## 🛡 Security Notes

- All routes are protected by login
- User sessions expire after 30 minutes of inactivity
- No sensitive data is stored in plain text (besides the 4-digit PIN and TOTP key for demo simplicity)

---

## Field Use

This app is designed to be:
- Easy to deploy
- Functional offline on LAN
- Friendly for warehouses, workshops, or mobile teams
