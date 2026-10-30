<p align="center">
  <img src="OT%20logo.png" alt="Ohr Temimim" width="180" />
</p>

<h1 align="center">Ohr Temimim School — Attendance System</h1>
<p align="center"><strong>אור תמימים</strong> · Student sign-in / sign-out app + admin panel</p>

---

A complete student attendance system for **Ohr Temimim School**:

- 📱 **Student mobile app** (`/mobile`) — a real Android **APK** (Expo / React Native). Each student enters their **Student ID** and taps **Sign In** or **Sign Out**.
- 🖥️ **Server + admin panel** (`/server`) — a Python **FastAPI** app that runs on **port 8000**, serving a JSON API for the app and a full web admin dashboard.

---

## Project layout

```
apk/
├── OT logo.png            # School logo (branding)
├── assets/logo.png        # Shared copy of the logo
├── mobile/                # Student APK (Expo / React Native)
│   ├── App.js             # Sign in / out screen
│   ├── src/config.js      # ← set SERVER_URL here
│   └── src/api.js
└── server/                # FastAPI server + admin panel (port 8000)
    ├── app/               # API, admin UI, models, templates
    ├── run.py             # start the server
    ├── seed_demo.py       # optional demo data
    └── requirements.txt
```

---

## 1. Run the server (admin panel + API)

Requires Python 3.11+.

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# (optional) add demo classes + students (IDs 1001–1006)
python seed_demo.py

# start on port 8000
python run.py
```

- **Admin panel:** http://localhost:8000/
- **API base:** http://localhost:8000/api
- **Default admin login:** `admin` / `admin123`  ← **change this in production!**

### Admin panel features
- Secure admin login (session-based)
- Dashboard: total students, present now, absent, classes, sign-ins today, recent activity
- **Students:** add / edit / delete, search, filter by class, manually toggle in/out
- **Attendance log:** filter by date and action (in/out)
- **Classes:** create / delete, assign students
- **Admin users:** add / delete admins (superadmin flag)
- **Audit log:** every admin action is recorded
- **CSV export:** students and attendance

### Configuration (environment variables)
| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8000` | Server port (keep 8000) |
| `SECRET_KEY` | dev key | **Change in production** (sessions + tokens) |
| `DEFAULT_ADMIN_USERNAME` | `admin` | First-run admin username |
| `DEFAULT_ADMIN_PASSWORD` | `admin123` | First-run admin password |
| `DATABASE_URL` | SQLite file | e.g. a Postgres URL |

---

## 2. Point the app at your server

Edit **`mobile/src/config.js`** and set `SERVER_URL`:

- Android emulator → `http://10.0.2.2:8000`
- Real phone on same Wi-Fi → `http://<your-computer-LAN-IP>:8000`
- Hosted server → `http://your-server-domain:8000`

> The server only uses **port 8000**, so keep `:8000` in the URL.

---

## 3. Build the APK

The app is an Expo project. Install tooling first:

```bash
cd mobile
npm install
```

### Option A — Cloud build (recommended, no Android SDK needed)
```bash
npm install -g eas-cli
eas login                      # free Expo account
eas build -p android --profile preview
```
EAS compiles it and gives you a link to download the **`.apk`**. Install it on any Android phone (allow "install from unknown sources").

### Option B — Local build (needs Android Studio / SDK)
```bash
npx expo run:android           # builds & installs on a connected device/emulator
# or a release APK:
npx expo prebuild
cd android && ./gradlew assembleRelease
# APK at: android/app/build/outputs/apk/release/app-release.apk
```

### Try it instantly without building (Expo Go)
```bash
cd mobile
npm install
npx expo start
```
Scan the QR code with the **Expo Go** app. (For a device, set `SERVER_URL` to your computer's LAN IP.)

---

## Quick test flow
1. Start the server and run `python seed_demo.py`.
2. Open the app, enter **`1001`**, tap **Check Status** → shows *Moshe Goldberg, Signed Out*.
3. Tap **Sign In** → confirmation appears; refresh the admin **Dashboard** → *Present Now* increases.
4. Tap **Sign Out** → status flips; the **Attendance** log shows both events.

---

<p align="center"><em>Ohr Temimim School · אור תמימים</em></p>
