# Weekly Prompt Update - Cron Job Setup

This document explains how to set up a weekly automated task to fetch and update AI/ML prompts from internet sources.

## Overview

The script `scripts/fetch_prompts_from_internet.py` fetches questions from Stack Overflow and other sources, categorizes them, and adds new prompts to `prompts.txt`. The total number of prompts is kept under 30,000.

**Schedule:** Every Monday at 2:00 AM  
**Script:** `scripts/fetch_prompts_from_internet.py`  
**Max Prompts:** 30,000

## Linux/macOS Setup

### Automatic Setup

Run the setup script:

```bash
chmod +x scripts/setup_cron.sh
./scripts/setup_cron.sh
```

### Manual Setup

1. Open your crontab:
   ```bash
   crontab -e
   ```

2. Add this line (adjust paths as needed):
   ```cron
   0 2 * * 1 cd /path/to/project && python3 scripts/fetch_prompts_from_internet.py >> logs/prompt_fetch.log 2>> logs/prompt_fetch_error.log
   ```

3. Save and exit.

### Verify

```bash
# View your crontab
crontab -l

# Check logs (after first run)
tail -f logs/prompt_fetch.log
```

## Windows Setup

### Automatic Setup (PowerShell as Administrator)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\setup_cron.ps1
```

### Manual Setup

1. Open Task Scheduler (search for "Task Scheduler" in Start menu)

2. Click "Create Basic Task" or "Create Task"

3. Configure:
   - **Name:** AIAlgoTeacher_WeeklyPromptUpdate
   - **Description:** Weekly update of AI/ML prompts from internet sources
   - **Trigger:** Weekly, Monday, 2:00 AM
   - **Action:** Start a program
     - Program: `python.exe` (or full path to your Python)
     - Arguments: `"E:\Python\Cursor\4\scripts\fetch_prompts_from_internet.py"`
     - Start in: `E:\Python\Cursor\4`

4. Save the task

## What the Script Does

1. **Fetches Questions:** Gets ML/AI questions from Stack Overflow (last 7 days)
2. **Filters:** Validates question format and content
3. **Deduplicates:** Removes prompts already in `prompts.txt`
4. **Categorizes:** Assigns algorithm type using existing categorization function
5. **Updates File:** Adds new prompts to `prompts.txt` (up to 30k total)
6. **Logs:** Records all activity to log files

## Logs

- **Success log:** `logs/prompt_fetch.log`
- **Error log:** `logs/prompt_fetch_error.log`

## Testing

Test the script manually before setting up cron:

```bash
# Linux/macOS
python3 scripts/fetch_prompts_from_internet.py

# Windows
python scripts/fetch_prompts_from_internet.py
```

## Monitoring

Check if the cron job is working:

```bash
# Linux/macOS - Check recent cron runs
grep CRON /var/log/syslog | tail -20

# Windows - Check Task Scheduler history
# Open Task Scheduler -> Task Scheduler Library -> AIAlgoTeacher_WeeklyPromptUpdate -> History
```

## Troubleshooting

### Python Not Found
- Ensure Python is in your PATH
- Use full path to Python in cron job/task

### Script Fails
- Check error log: `logs/prompt_fetch_error.log`
- Ensure `requests` library is installed: `pip install requests`
- Verify internet connectivity

### Permissions
- Ensure script is executable (Linux/macOS): `chmod +x scripts/fetch_prompts_from_internet.py`
- Ensure project directory is writable

### Prompts Not Adding
- Check if already at 30k limit
- Verify deduplication is working correctly
- Check Stack Overflow API rate limits

## Customization

Edit `scripts/fetch_prompts_from_internet.py` to customize:

- `MAX_TOTAL_PROMPTS`: Maximum total prompts (default: 30000)
- `DAYS_TO_FETCH`: How many days back to fetch (default: 7)
- `MAX_QUESTIONS_PER_SOURCE`: Limit per source (default: 100)

## Adding More Sources

The script is designed to be extensible. To add Reddit or other sources:

1. Implement fetch function (e.g., `fetch_reddit_questions()`)
2. Add to `main()` function
3. See `docs/PROMPT_FETCHING_ALGORITHM.md` for details

