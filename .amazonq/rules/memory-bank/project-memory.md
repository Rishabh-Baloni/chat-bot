# Project Memory Bank: D-Drive Environment Setup

## Project Overview
**Purpose**: Configure Windows development environment to use D: drive instead of C: drive for all installations, caches, and downloads to preserve C: drive space.

## Key Components

### 1. PowerShell Setup Script (`setup-environment.ps1`)
- **Function**: Automated configuration script for D: drive environment
- **Key Actions**:
  - Creates directory structure on D: drive
  - Sets persistent user environment variables
  - Configures pip.ini for D: drive usage
  - Updates PYTHONPATH

### 2. Installation Rules (`INSTALLATION_RULES.md`)
- **Function**: Reference guide for D: drive installation practices
- **Covers**: Python/pip, NPM/Node, general download rules

## Environment Variables Set
```
PIP_CACHE_DIR=D:\pip-cache
PYTHONUSERBASE=D:\Python-Packages
npm_config_cache=D:\npm-cache
npm_config_prefix=D:\npm-global
PYTHONPATH=D:\Python-Packages\Lib\site-packages
```

## Directory Structure Created
```
D:\
├── pip-cache/
├── Python-Packages/
│   └── Lib/site-packages/
├── Downloads/
├── venvs/
├── npm-cache/
└── npm-global/
```

## Critical Usage Patterns
- **Pip installs**: Always use `--target D:\Python-Packages\Lib\site-packages`
- **Virtual envs**: Create in `D:\venvs\`
- **Git repos**: Clone to `D:\Projects\`
- **Downloads**: Default to `D:\Downloads\`

## Project Status
- **Type**: Environment configuration utility
- **Language**: PowerShell
- **Target OS**: Windows
- **Last Updated**: January 2026