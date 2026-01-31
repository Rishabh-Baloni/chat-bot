# Installation Rules - No C: Drive Usage

**IMPORTANT**: All downloads, pip installations, and package caches should use D: drive.

## Python/Pip Configuration

### 1. Set Environment Variables (Permanent)
Add these to your Windows System Environment Variables:

```
PIP_CACHE_DIR=D:\pip-cache
PYTHONUSERBASE=D:\Python-Packages
```

### 2. Pip Configuration File
Location: `%APPDATA%\pip\pip.ini` (or create at `D:\Projects\pip.ini`)

```ini
[global]
cache-dir = D:\pip-cache
target = D:\Python-Packages\Lib\site-packages

[install]
user = false
prefix = D:\Python-Packages
```

### 3. Always Use These Pip Flags
When installing packages, always use:
```bash
pip install <package> --target D:\Python-Packages\Lib\site-packages --cache-dir D:\pip-cache
```

## NPM/Node Configuration (if needed)
```
npm config set cache D:\npm-cache
npm config set prefix D:\npm-global
```

## General Download Rules
- Browser downloads: Set default to `D:\Downloads`
- Git repositories: Clone to `D:\Projects`
- Virtual environments: Create in `D:\venvs`

## Quick Reference Commands

### Create Virtual Environment on D:
```bash
python -m venv D:\venvs\myproject
```

### Install with specific target:
```bash
pip install --target D:\Python-Packages\Lib\site-packages packagename
```

---
**Last Updated**: January 26, 2026
