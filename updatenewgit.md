# How to Update Server Files from GitHub

This guide explains how to update the files on your DigitalOcean server with the latest code from GitHub.

## Method 1: Using Git Pull (Recommended)

This is the simplest method if you've already cloned the repository on your server.

### Steps:

1. **SSH into your server:**
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

2. **Navigate to the application directory:**
   ```bash
   cd /opt/content-generator
   ```

3. **Check current status:**
   ```bash
   git status
   git log --oneline -5
   ```

4. **Pull the latest changes from GitHub:**
   ```bash
   git pull origin main
   ```

5. **If you have local changes that conflict:**
   - **Option A: Stash local changes** (save them for later)
     ```bash
     git stash
     git pull origin main
     git stash pop  # If you want to reapply your changes
     ```
   
   - **Option B: Discard local changes** (replace with GitHub version)
     ```bash
     git fetch origin
     git reset --hard origin/main
     ```
     **⚠️ WARNING:** This will permanently delete any local changes!

6. **Update Python dependencies (if requirements.txt changed):**
   ```bash
   cd backend
   source venv/bin/activate
   pip install -r requirements.txt --upgrade
   deactivate
   cd ..
   ```

7. **Restart the service:**
   ```bash
   sudo systemctl restart content-generator
   ```

8. **Verify the service is running:**
   ```bash
   sudo systemctl status content-generator
   ```

9. **Check logs if there are issues:**
   ```bash
   sudo journalctl -u content-generator -n 50 --no-pager
   ```

## Method 2: Complete Re-clone (Fresh Start)

Use this method if you want to completely replace everything with the GitHub version.

### Steps:

1. **SSH into your server:**
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

2. **Stop the service:**
   ```bash
   sudo systemctl stop content-generator
   ```

3. **Backup your `.env` file (IMPORTANT!):**
   ```bash
   cp /opt/content-generator/backend/.env /opt/content-generator/backend/.env.backup
   ```

4. **Backup your `prompts.json` file (if you've customized prompts):**
   ```bash
   cp /opt/content-generator/backend/prompts.json /opt/content-generator/backend/prompts.json.backup
   ```

5. **Remove the old directory:**
   ```bash
   cd /opt
   rm -rf content-generator
   ```

6. **Clone fresh from GitHub:**
   ```bash
   git clone https://github.com/RuffBudda/21SIXTY-Content.git content-generator
   cd content-generator
   ```

7. **Restore your `.env` file:**
   ```bash
   cp /opt/content-generator/backend/.env.backup /opt/content-generator/backend/.env
   ```

8. **Restore your `prompts.json` (if you had custom prompts):**
   ```bash
   cp /opt/content-generator/backend/prompts.json.backup /opt/content-generator/backend/prompts.json
   ```

9. **Set up virtual environment and install dependencies:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   deactivate
   cd ..
   ```

10. **Fix permissions:**
    ```bash
    sudo chown -R www-data:www-data /opt/content-generator
    sudo chmod -R 755 /opt/content-generator
    sudo chmod -R 775 /opt/content-generator/backend/uploads
    ```

11. **Start the service:**
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl start content-generator
    sudo systemctl enable content-generator
    ```

12. **Verify it's running:**
    ```bash
    sudo systemctl status content-generator
    ```

## Method 3: Using GitHub Actions (Automatic)

If you've set up GitHub Actions (see DEPLOYMENT.md Step 24), the deployment happens automatically when you push to GitHub. Just:

1. **Push your changes to GitHub** (from your local machine)
2. **Check GitHub Actions** to see deployment progress
3. **Verify on server** that the service restarted

## Troubleshooting

### "Permission denied" errors

```bash
# Fix ownership
sudo chown -R www-data:www-data /opt/content-generator
```

### "Service won't start" after update

```bash
# Check logs
sudo journalctl -u content-generator -n 100 --no-pager

# Check if .env file exists and has correct values
sudo cat /opt/content-generator/backend/.env

# Verify virtual environment
ls -la /opt/content-generator/backend/venv
```

### "Module not found" errors

```bash
# Reinstall dependencies
cd /opt/content-generator/backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
deactivate
```

### Conflict with local changes

If you have local changes you want to keep:
1. Make a backup first
2. Use `git stash` to save changes
3. Pull from GitHub
4. Manually merge any needed changes from the backup

## What Gets Updated

When you pull from GitHub, these files will be updated:
- ✅ All Python files (`backend/*.py`)
- ✅ Frontend files (`frontend/*.html`, `frontend/*.js`, `frontend/*.css`)
- ✅ Configuration files (`.github/workflows/*`, `nginx/*`, `systemd/*`)
- ✅ `requirements.txt` and other project files

## What Stays the Same (Not Updated)

These files are NOT tracked in git and won't be overwritten:
- ❌ `.env` file (your API keys and passwords)
- ✅ `prompts.json` (IS tracked, but you can backup if customized)
- ❌ `uploads/` directory (MP3 files)
- ❌ Any files in `.gitignore`

## Quick Update Script

You can create a script to automate updates:

```bash
#!/bin/bash
# Save as: /opt/update-content-gen.sh

cd /opt/content-generator
git pull origin main
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade --quiet
deactivate
cd ..
sudo systemctl restart content-generator
echo "Update complete! Check status with: sudo systemctl status content-generator"
```

Make it executable:
```bash
chmod +x /opt/update-content-gen.sh
```

Then update with:
```bash
sudo /opt/update-content-gen.sh
```

