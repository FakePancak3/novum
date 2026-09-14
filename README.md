<picture>
  <source media="(prefers-color-scheme: dark)" srcset="banner-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="banner-light.png">
  <img alt="NOVUM" src="banner-light.png">
</picture>

[![License](https://img.shields.io/github/license/FakePancak3/novum)](https://github.com/FakePancak3/novum/blob/main/LICENSE)
[![Latest Release](https://img.shields.io/github/v/release/FakePancak3/novum)](https://github.com/FakePancak3/novum/releases)
[![Downloads](https://img.shields.io/github/downloads/FakePancak3/novum/total)](https://github.com/FakePancak3/novum/releases)

A minimal, dark-themed auto-clicker with naturally varying click speed
and a rebindable global hotkey.

> [!IMPORTANT]
> Novum is an **open-source hobby project.**
> **The Windows executable is currently not code signed so Windows may show a SmartScreen warning** because the application does not have an established publisher reputation.
> **This does not mean the warning should be ignored blindly.**
> If you are uncomfortable running the prebuilt executable, you can inspect the source code and build Novum yourself using the instructions below.
> The source code used to build Novum is available in this repository.

## Features

- Clicking speed drifts naturally between your set min/max CPS instead
  of firing at one fixed rate.
- Global hotkey toggle (default **F6**) works even when another
  window or game is focused.
- Click-to-rebind hotkey, including modifier combos (e.g. `Ctrl+H`).
- Small, clean, dark UI. No installer, no bloat.

## Download

Get the latest `NOVUM.exe` from the [Releases](../../releases) page.
No installation needed, just run it.

**SHA-256 checksum for the latest release:** see the checksum listed
on that releases page. Verify it in PowerShell with:

```powershell
Get-FileHash NOVUM.exe -Algorithm SHA256
```

If the hash doesn't match what's listed on the release page, don't run
the file re-download from the official Releases link above.

## Usage

1. Run `NOVUM.exe`.
2. Set **Min CPS** and **Max CPS** (defaults: 8 / 12).
3. Click **START**, then move your mouse to where you want it to
   click. Theres a short delay after pressing Start specifically so
   you have time to move the cursor off the button.
4. Press **F6** anytime to toggle clicking on/off or click **STOP**.
5. To change the hotkey: click the current key next to "Toggle key,"
   then press any key (or key combo) you want to use instead.

## ⚠️ A couple of things to know before using this

- **Antivirus warnings:** Novum is currently unsigned, so Windows may display a Microsoft Defender SmartScreen warning. The source code     is publicly available, and each release includes a SHA-256 checksum so you can verify the downloaded file.
- **Terms of service:** Many games and applications explicitly
  prohibit automated input like auto-clicking, and using one can get
  you penalized or banned. Thats between you and whatever
  game/app/service you use this with use your own judgment and
  check the rules first.
- **No warranty:** this is a free hobby project provided as-is, with
  no guarantee of fitness for any particular purpose.
- **AI Usage:** Ai was used for making SOME parts of this project, i will not deny that.

## Building from source

If you'd rather build it yourself than trust a prebuilt binary:

```bash
git clone https://github.com/FakePancak3/novum.git
cd novum
pip install -r requirements.txt
python main.py
```

To build your own standalone exe:

```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name NOVUM --icon icon.ico --add-data "icon.ico;." main.py
```

Your exe will be in `dist/NOVUM.exe`.

## License
MIT
