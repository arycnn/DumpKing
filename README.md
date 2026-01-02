# 👑 DumpKing v3.1

**DumpKing** is an advanced, open-source memory manipulation suite for Android. It combines a GameGuardian-style memory scanner with a fully automated extraction suite for Unity (IL2CPP) games.

It works by injecting a lightweight Smali server (`MemorySpy`) into the target APK, allowing you to scan, edit, freeze, and dump memory in real-time from your PC via ADB.

## ⚡ Features

* **Remote Memory Scanning:** Search for Integers (DWORD) and Hex patterns instantly.
* **Live Memory Watcher:** Monitor values changing in real-time.
* **God Mode Tools:** Freeze values (HP, Ammo, Timer) or edit them in batches.
* **Smart Dumping:** Bypasses socket limits to dump massive memory regions (100MB+) without crashing the app.
* **Automated Il2Cpp Extractor:** One-click automation that:
1. Hunts down and dumps the decrypted `global-metadata.dat` (even if hidden).
2. Locates and dumps `libil2cpp.so`.
3. Runs **Il2CppDumper** automatically to generate `dump.cs`.



---

## 🛠️ Prerequisites

1. **Python 3.x** ([Download Here](https://www.python.org/downloads/))
2. **ADB (Android Debug Bridge)** installed and added to your PATH.
3. **Java (JRE/JDK)** installed (required for APKEditor).
4. **Target APK** (The game you want to hack).

---

## 🚀 Installation & Injection

To use DumpKing, you must inject the "Spy" server into the target APK.

### 1. Decompile the APK

We recommend using **APKEditor** for the cleanest decompile/rebuild process.

* **[Download APKEditor](https://github.com/REAndroid/APKEditor)**

Run the following command to decompile your target game:

```bash
java -jar APKEditor.jar d -i TargetGame.apk

```

### 2. Inject the Smali Files

1. Navigate to the `Dump King Smali Files (Install)/spy` folder in this repository.
2. Copy the entire `spy` folder.
3. Go to your decompiled APK folder (e.g., `TargetGame/smali/classes/com/`).
4. Paste the `spy` folder here.
* *Path should look like:* `TargetGame/smali/classes/com/spy/MemorySpy.smali`



### 3. Hook the Entry Point

You need to start the Spy when the app launches.

1. Find the Main Activity of the game (check `AndroidManifest.xml`).
2. Open the `.smali` file for that activity.
3. Search for the `onCreate` method.
4. Add this line right before `return-void`:
```smali
invoke-static {}, Lcom/spy/MemorySpy;->start()V

```



### 4. Rebuild & Install

Rebuild the APK using APKEditor:

```bash
java -jar APKEditor.jar b -i TargetGame_Folder

```

Sign the APK (using `uber-apk-signer` or similar), then install it on your device.

---

## ⚙️ Setup for Automation

For the **Create Dump.cs** feature to work, you need to set up the folder structure on your PC.

1. Download the latest release of **Il2CppDumper**:
* **[Download Il2CppDumper](https://github.com/Perfare/Il2CppDumper/releases)**


2. Extract it into a folder named `Il2CppDumper` **in the same directory** as `DumpKing.py`.

**Your folder structure must look like this:**

```text
DumpKing_Folder/
│
├── DumpKing.py               # The main script
│
└── Il2CppDumper/             # Folder you created
    ├── Il2CppDumper.exe      # The executable
    ├── Il2CppDumper.deps.json
    └── ...

```

---

## 🎮 How to Use

### 1. Connect

Ensure your device is connected via USB and the game is running.
Forward the internal port so Python can talk to the game:

```bash
adb forward tcp:12345 tcp:12345

```

### 2. Run DumpKing

```bash
python DumpKing.py

```

### 3. Generate Dump.cs (The Easy Way)

If you are hacking a Unity game and want the offsets:

1. Select **Option [8] Create Dump.cs (Automated)** from the main menu.
2. Select **Option [4] Run All One by One**.
3. Watch the magic happen:
* It scans memory for the hidden, decrypted metadata header (`AF 1B B1 FA`).
* It dumps it to `Dumped MetaData/global-metadata.dat`.
* It finds and dumps `libil2cpp.so` to `Pulled libil2cpp/`.
* It launches `Il2CppDumper.exe` automatically.



---

## 📂 Output

All dumped files are saved automatically in the `Dumped Memory Tools` folder, organized by category.

* **Metadata:** `Dumped MetaData/`
* **Binaries:** `Pulled libil2cpp/`
* **Manual Dumps:** `Dumped Memory Tools/`

---

## ⚖️ Disclaimer

This tool is open source and created for educational purposes and security research only. Use it to analyze apps you own or have permission to test. I am not responsible for banned accounts or broken APKs.
