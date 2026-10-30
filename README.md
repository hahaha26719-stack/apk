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

> **On ARM boards (Banana Pi / Raspberry Pi):** pip compiles `bcrypt` from source,
> which needs build tools. Install them first:
> ```bash
> sudo apt update
> sudo apt install -y python3-dev python3-venv build-essential libffi-dev pkg-config cargo rustc
> ```
> (The `deploy/install.sh` script does this for you automatically.)

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

### Run the server as a service on boot (Linux / systemd)
To have the server start automatically on every boot and restart if it crashes:

```bash
cd server
sudo bash deploy/install.sh
```

This creates a Python virtualenv, generates a random `SECRET_KEY` in `server/.env`,
installs a **systemd** service called `ohr-temimim`, and starts it on port 8000.

```bash
sudo systemctl status ohr-temimim     # check it's running
sudo journalctl -u ohr-temimim -f     # live logs
sudo systemctl restart ohr-temimim    # restart
```

> After install, edit `server/.env` to set a real `DEFAULT_ADMIN_PASSWORD`, then
> `sudo systemctl restart ohr-temimim`.

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

The native **`mobile/android/`** Gradle project is already generated and committed,
so you can build the APK directly with **Gradle** — no Expo cloud account needed.

### Prerequisites
- **JDK 17** (Android Gradle Plugin does **not** support JDK 21+/25).
  The easiest way is to install **Android Studio**, which bundles JDK 17 and the SDK.
- **Android SDK** with platform **34** and build-tools (Android Studio installs these).
- Point Gradle at your SDK by creating `mobile/android/local.properties`:
  ```properties
  sdk.dir=/Users/you/Library/Android/sdk        # macOS
  # sdk.dir=C:\\Users\\you\\AppData\\Local\\Android\\Sdk   # Windows
  # sdk.dir=/home/you/Android/Sdk                # Linux
  ```

### Option A — Local build with Gradle (`./gradlew`)
```bash
cd mobile
npm install            # install JS dependencies (needed once; Gradle bundles the JS)

cd android
./gradlew assembleRelease            # macOS/Linux   (Windows: gradlew.bat assembleRelease)
```
The installable APK is written to:
```
mobile/android/app/build/outputs/apk/release/app-release.apk
```
Copy it to an Android phone and install (allow "install from unknown sources").

> The release build is signed with the bundled **debug keystore** so it installs immediately.
> For the Google Play Store, generate your own keystore and update the `release` `signingConfig`
> in `mobile/android/app/build.gradle` — see https://reactnative.dev/docs/signed-apk-android

> If you ever change `app.json` (name, icon, package), regenerate the native project with
> `npx expo prebuild --platform android` from the `mobile/` folder.

### Option B — Cloud build (no Android SDK needed)
```bash
cd mobile && npm install
npm install -g eas-cli
eas login                      # free Expo account
eas build -p android --profile preview
```
EAS compiles it and gives you a link to download the **`.apk`**.

### Launch the app automatically on device boot (kiosk mode)
The APK is configured to **start automatically when the Android device finishes booting**
— ideal for a dedicated attendance tablet at the school entrance. This is handled by a
`BootReceiver` (see `mobile/android/app/src/main/java/.../BootReceiver.kt`) and the
`RECEIVE_BOOT_COMPLETED` permission.

Notes:
- The user must open the app **once** after installing (Android blocks auto-start until
  the app has been launched at least once).
- On some phones (Xiaomi, Oppo, Huawei, etc.) you must also enable **"Autostart"** for
  the app in the system settings — manufacturer battery managers block boot receivers by default.
- For a true locked-down kiosk, pair this with Android **Screen Pinning** (Settings →
  Security → Screen pinning) or a dedicated kiosk/MDM launcher.

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
