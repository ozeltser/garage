# Self-Hosted GitHub Actions Runner Setup Guide

This guide walks you through setting up a GitHub Actions self-hosted runner on your Raspberry Pi so that the Garage web app is automatically deployed whenever code is merged to `main`.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Enable Branch Protection on GitHub](#2-enable-branch-protection-on-github)
3. [Generate a Runner Registration Token](#3-generate-a-runner-registration-token)
4. [Download and Install the Runner on the Pi](#4-download-and-install-the-runner-on-the-pi)
5. [Configure the Runner](#5-configure-the-runner)
6. [Install the Runner as a Systemd Service](#6-install-the-runner-as-a-systemd-service)
7. [Configure Sudoers for Deployments](#7-configure-sudoers-for-deployments)
8. [Bootstrap the First Deploy](#8-bootstrap-the-first-deploy)
9. [Verify the Full Pipeline](#9-verify-the-full-pipeline)
10. [Troubleshooting](#10-troubleshooting)
11. [Runner Maintenance](#11-runner-maintenance)

---

## 1. Prerequisites

Before you begin, make sure the following are in place on your Raspberry Pi.

### Hardware and OS

- Raspberry Pi 3B+ or newer (Pi 4/5 recommended)
- Raspberry Pi OS **64-bit** (Bookworm or later)

Verify your architecture (must say `aarch64`):

```bash
uname -m
# Expected output: aarch64
```

Verify your OS version:

```bash
cat /etc/os-release | grep PRETTY_NAME
# Expected output: PRETTY_NAME="Debian GNU/Linux 12 (bookworm)" (or similar)
```

### Application Already Deployed

The garage app must already be installed and running at `/opt/garage/app`. If you haven't done this yet, follow `PRODUCTION.md` or run `install_production.sh` first.

Verify:

```bash
systemctl status garage.service
# Should show "active (running)"

curl -sf http://127.0.0.1:5000/login
# Should return HTML
```

### Install `uv` (Python Package Manager)

The deploy pipeline uses `uv` to sync dependencies. Install it system-wide:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, verify it's available:

```bash
uv --version
# Should print the uv version, e.g., uv 0.5.x
```

> **Note:** If `uv` was installed to `~/.local/bin`, copy it to a system-wide location so all users (including `garage`) can access it:
>
> ```bash
> sudo cp ~/.local/bin/uv /usr/local/bin/uv
> sudo cp ~/.local/bin/uvx /usr/local/bin/uvx 2>/dev/null || true
> ```
>
> Alternatively, add it to PATH via a profile script (requires logging out and back in for the change to take effect):
>
> ```bash
> echo 'export PATH="$HOME/.local/bin:$PATH"' | sudo tee /etc/profile.d/uv.sh
> # You must log out and log back in (or open a new shell) for this to take effect
> ```

### Install Required Tools

```bash
sudo apt update
sudo apt install -y curl jq
```

### Network

The runner connects **outbound** to GitHub — no inbound ports or port forwarding are required. Your Pi just needs regular internet access.

Verify connectivity:

```bash
curl -sf https://github.com > /dev/null && echo "GitHub is reachable" || echo "Cannot reach GitHub"
```

---

## 2. Enable Branch Protection on GitHub

Branch protection ensures that the only way code reaches `main` is through a merged pull request with passing tests. This is critical — the deploy workflow triggers on any push to `main`, so you must prevent direct pushes.

### Option A — GitHub Web UI (Point-and-Click)

1. Go to your repository on **github.com**
2. Click the **Settings** tab (gear icon in the top navigation bar)
3. In the left sidebar, scroll down to **Code and automation** and click **Branches**
4. Under **Branch protection rules**, click **Add branch protection rule** (or **Add classic branch protection rule**)
5. In the **Branch name pattern** field, type: `main`
6. Check the following boxes:
   - **Require a pull request before merging**
     - Check **Require approvals** and set the number (1 is fine for a personal project)
   - **Require status checks to pass before merging**
     - Click **Search for status checks** and add:
       - `pytest (3.11)`
       - `pytest (3.12)`
     - Check **Require branches to be up to date before merging**
   - **Do not allow bypassing the above settings** (optional but recommended)
7. Click **Create** (or **Save changes**)

### Option B — `gh` CLI

```bash
# Install gh CLI if not already installed
sudo apt install gh
gh auth login  # Follow the interactive prompts to authenticate

# Create branch protection rule
gh api repos/OWNER/REPO/branches/main/protection \
  --method PUT \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["pytest (3.11)", "pytest (3.12)"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1
  },
  "restrictions": null
}
EOF
```

Replace `OWNER/REPO` with your actual GitHub username and repository name (e.g., `ozeltser/garage`).

### Verify Branch Protection

**Web UI:** Go to **Settings** → **Branches** — you should see `main` listed with a shield icon.

**CLI:**

```bash
gh api repos/OWNER/REPO/branches/main/protection --jq '{
  required_reviews: .required_pull_request_reviews.required_approving_review_count,
  status_checks: .required_status_checks.contexts
}'
```

---

## 3. Generate a Runner Registration Token

You need a one-time registration token to connect the runner to your repository. This token is valid for **1 hour**.

### Option A — GitHub Web UI (Point-and-Click)

1. Go to your repository on **github.com**
2. Click the **Settings** tab (gear icon)
3. In the left sidebar, under **Code and automation**, click **Actions**
4. In the Actions submenu, click **Runners**
5. Click the green **New self-hosted runner** button
6. On the next page:
   - Under **Runner image**, select **Linux**
   - Under **Architecture**, select **ARM64**
7. You will see a page with setup instructions. Look for the `--token` value in the **Configure** section — it looks like: `AABCDEFGHIJKLMNOPQRSTUVWXYZ234`
8. **Copy this token** — you will need it in the next step
9. **Do not close this page yet** — it also shows the download URL you'll need

### Option B — `gh` CLI

```bash
# Generate a registration token (requires admin access to the repo)
TOKEN=$(gh api repos/OWNER/REPO/actions/runners/registration-token \
  --method POST \
  --jq '.token')

echo "Registration token: $TOKEN"
echo "This token expires in 1 hour — use it promptly."
```

Replace `OWNER/REPO` with your actual repository path (e.g., `ozeltser/garage`).

---

## 4. Download and Install the Runner on the Pi

Run these commands **on your Raspberry Pi** (via SSH or directly).

### Create the Runner Directory

```bash
sudo mkdir -p /opt/github-runner
sudo chown garage:garage /opt/github-runner
```

### Download the Runner

Check the [GitHub Actions Runner releases page](https://github.com/actions/runner/releases) for the latest version. As of writing, the latest is v2.321.0. Download the **ARM64** variant:

```bash
cd /opt/github-runner

# Download (replace version number with latest if newer)
curl -o actions-runner-linux-arm64.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-linux-arm64-2.321.0.tar.gz
```

> **How to find the latest version:** Go to https://github.com/actions/runner/releases and look for the file named `actions-runner-linux-arm64-X.Y.Z.tar.gz`. Or via CLI:
>
> ```bash
> LATEST=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name' | sed 's/^v//')
> echo "Latest runner version: $LATEST"
> curl -o actions-runner-linux-arm64.tar.gz -L \
>   "https://github.com/actions/runner/releases/download/v${LATEST}/actions-runner-linux-arm64-${LATEST}.tar.gz"
> ```

### Extract

```bash
tar xzf actions-runner-linux-arm64.tar.gz
```

### Install System Dependencies

The runner needs some system libraries. Install them:

```bash
sudo ./bin/installdependencies.sh
```

This may take a few minutes. It installs .NET runtime dependencies required by the runner.

### Verify Installation

```bash
./run.sh --version
# Should print the runner version, e.g., 2.321.0
```

---

## 5. Configure the Runner

Run the configuration **as the `garage` user** (the same user that owns the app):

```bash
# Switch to the garage user
sudo su - garage -s /bin/bash

cd /opt/github-runner

./config.sh \
  --url https://github.com/OWNER/REPO \
  --token YOUR_TOKEN_HERE \
  --labels self-hosted,raspberry-pi \
  --name garage-pi-runner \
  --work _work \
  --runnergroup Default
```

Replace:
- `OWNER/REPO` with your repository (e.g., `ozeltser/garage`)
- `YOUR_TOKEN_HERE` with the registration token from Step 3

### Interactive Prompts

If you didn't provide all flags, the config script will prompt you:

| Prompt | What to Enter |
|--------|---------------|
| "Enter the name of the runner group" | Press **Enter** to accept `Default` |
| "Enter the name of runner" | Type `garage-pi-runner` (or press **Enter** for the hostname) |
| "Enter any additional labels" | Type `raspberry-pi` and press **Enter** |
| "Enter name of work folder" | Press **Enter** to accept `_work` |

### Exit Back to Your Regular User

```bash
exit
```

### Verify on GitHub (Point-and-Click)

1. Go to your repository on **github.com**
2. Click **Settings** → **Actions** → **Runners**
3. You should see `garage-pi-runner` in the list
4. Status should show **Idle** (with a green circle)
5. Labels should include: `self-hosted`, `Linux`, `ARM64`, `raspberry-pi`

### Verify via `gh` CLI

```bash
gh api repos/OWNER/REPO/actions/runners \
  --jq '.runners[] | {name, status, labels: [.labels[].name]}'
```

Expected output:

```json
{
  "name": "garage-pi-runner",
  "status": "online",
  "labels": ["self-hosted", "Linux", "ARM64", "raspberry-pi"]
}
```

---

## 6. Install the Runner as a Systemd Service

The runner must start automatically on boot and stay running. Install it as a systemd service:

```bash
cd /opt/github-runner

# Install the service (runs as the garage user)
sudo ./svc.sh install garage

# Start the service
sudo ./svc.sh start

# Verify it's running
sudo ./svc.sh status
```

### What Each Command Does

| Command | Effect |
|---------|--------|
| `sudo ./svc.sh install garage` | Creates a systemd service file that runs the runner as the `garage` user |
| `sudo ./svc.sh start` | Starts the runner service immediately |
| `sudo ./svc.sh status` | Shows whether the runner is active and recent log output |

### Verify the Service

```bash
# Check systemd status
systemctl status actions.runner.*.service

# View live logs
journalctl -u actions.runner.*.service -f
# Press Ctrl+C to stop following logs
```

The runner should show "Listening for Jobs" in the logs.

### Stopping and Uninstalling (If Needed Later)

```bash
cd /opt/github-runner

# Stop the service
sudo ./svc.sh stop

# Uninstall the service (removes the systemd unit)
sudo ./svc.sh uninstall
```

---

## 7. Configure Sudoers for Deployments

The deploy script (`deploy.sh`) runs as the `garage` user but needs to restart the `garage.service` systemd unit. This requires **passwordless sudo** for specific commands only.

### Create the Sudoers File

```bash
sudo visudo -f /etc/sudoers.d/garage-deploy
```

Paste the following content exactly:

```
# Allow the garage user to manage the garage.service without a password.
# This is required by the automated deploy script (deploy.sh).
garage ALL=(root) NOPASSWD: /bin/systemctl restart garage.service
garage ALL=(root) NOPASSWD: /bin/systemctl status garage.service
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter` in nano).

### Why This Is Safe

- The sudoers rules are scoped to **only** the two systemctl commands listed above (restart and status)
- The `garage` user cannot run arbitrary commands as root
- The `NOPASSWD` flag is required because the GitHub Actions runner runs non-interactively (there is no terminal to type a password)

### Verify Sudoers

```bash
# Switch to the garage user
sudo su - garage -s /bin/bash

# Test that both allowed commands work without a password prompt
sudo -n systemctl status garage.service
# Should show the service status without asking for a password

sudo -n systemctl restart garage.service
# Should restart the service without asking for a password

# Verify arbitrary commands are still denied
sudo -n ls /root
# Should fail with "a password is required"

exit
```

---

## 8. Bootstrap the First Deploy

The automated deploy pipeline calls `deploy.sh`, which must already exist on the Pi before the first automated run. This is a one-time bootstrapping step.

### Step 1: Pull the Latest Code

```bash
sudo su - garage -s /bin/bash
cd /opt/garage/app

# Fetch and apply the latest code (which includes deploy.sh)
git fetch origin main
git reset --hard origin/main
```

### Step 2: Create the `.venv` with uv

The project has migrated from `pip`/`requirements.txt` to `uv`. This creates a `.venv/` directory (replacing the old `venv/`):

```bash
cd /opt/garage/app
uv sync --frozen
```

Verify the virtual environment was created:

```bash
ls -la .venv/bin/python
# Should show the Python binary
```

### Step 3: Update the Installed Service File

The `garage.service` file in the repo now references `.venv/` instead of `venv/`. Copy it to systemd:

```bash
exit  # back to your regular user

sudo cp /opt/garage/app/garage.service /etc/systemd/system/garage.service
sudo systemctl daemon-reload
sudo systemctl restart garage.service
```

### Step 4: Verify the App Works

```bash
# Check service status
sudo systemctl status garage.service

# Health check
curl -sf http://127.0.0.1:5000/login > /dev/null && echo "App is healthy" || echo "App is NOT responding"
```

### Step 5: Test the Deploy Script Manually

Run `deploy.sh` once manually to verify everything works end-to-end:

```bash
sudo su - garage -s /bin/bash
cd /opt/garage/app
bash deploy.sh
```

Check the deploy log:

```bash
cat /opt/garage/deploy.log
```

You should see `DEPLOY SUCCEEDED` at the end.

```bash
exit
```

---

## 9. Verify the Full Pipeline

Now test the entire automated flow: code change → PR → tests pass → merge → auto-deploy.

### Step 1: Create a Test Branch and PR

**Web UI:**

1. Go to your repository on **github.com**
2. Navigate to any file (e.g., `README.md`)
3. Click the pencil icon (edit)
4. Make a trivial change (e.g., add a blank line at the end)
5. Click **Commit changes…**
6. Select **Create a new branch for this commit and start a pull request**
7. Name the branch something like `test/verify-cd-pipeline`
8. Click **Propose changes**
9. On the PR page, click **Create pull request**

**CLI:**

```bash
cd /home/user/garage  # or wherever your local clone is

git checkout -b test/verify-cd-pipeline
echo "" >> README.md
git add README.md
git commit -m "test: verify CD pipeline"
git push -u origin test/verify-cd-pipeline

# Create the PR
gh pr create --title "Test: Verify CD pipeline" --body "Trivial change to test the automated deploy pipeline."
```

### Step 2: Wait for Tests to Pass

**Web UI:**

1. On the PR page, scroll down to the **Checks** section
2. Wait for `pytest (3.11)` and `pytest (3.12)` to show green checkmarks
3. This usually takes 2-3 minutes

**CLI:**

```bash
gh pr checks
# Wait until all checks show ✓
```

### Step 3: Merge the PR

**Web UI:**

1. Once all checks pass, click the green **Merge pull request** button
2. Click **Confirm merge**
3. Optionally click **Delete branch** to clean up

**CLI:**

```bash
gh pr merge --merge --delete-branch
```

### Step 4: Watch the Deploy

**Web UI:**

1. Go to the **Actions** tab in your repository
2. You should see a new workflow run for **Deploy to Raspberry Pi**
3. Click on it to see the progress
4. The **test** jobs run first (on GitHub's servers)
5. Once they pass, the **deploy** job runs (on your Pi)
6. The deploy job should complete with a green checkmark

**On the Pi** (via SSH):

```bash
# Watch the deploy log in real-time
tail -f /opt/garage/deploy.log
```

### Step 5: Verify the Deploy

```bash
# Check that the latest commit is deployed
cd /opt/garage/app
git log --oneline -1
# Should show your test commit

# Health check
curl -sf http://127.0.0.1:5000/login > /dev/null && echo "App is healthy" || echo "App is NOT responding"
```

---

## 10. Troubleshooting

### Runner Shows "Offline" on GitHub

**Symptoms:** The runner appears on the Runners page but shows a grey or red status.

**Diagnosis:**

```bash
# Check the systemd service
systemctl status actions.runner.*.service

# Check for errors in the logs
journalctl -u actions.runner.*.service -n 50 --no-pager
```

**Common fixes:**

| Issue | Fix |
|-------|-----|
| Service not running | `cd /opt/github-runner && sudo ./svc.sh start` |
| Network connectivity | `curl -sf https://github.com > /dev/null && echo OK` |
| DNS resolution | `ping github.com` — if it fails, check `/etc/resolv.conf` |
| Runner was idle too long | Restart the service: `sudo ./svc.sh stop && sudo ./svc.sh start` |

### Deploy Fails with "uv not found"

`uv` must be installed system-wide or in a location available to the `garage` user's PATH.

```bash
# Check where uv is installed
which uv
# If not found, install it:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Make sure it's in PATH for the garage user
sudo su - garage -s /bin/bash -c "which uv"
# If not found, add to PATH:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> /opt/garage/.bashrc
```

### Permission Denied on `systemctl restart`

**Symptoms:** The deploy log shows `sudo: a password is required`.

**Fix:** Verify the sudoers file exists and is correct:

```bash
sudo cat /etc/sudoers.d/garage-deploy
# Should show the four NOPASSWD rules

# Test it
sudo su - garage -s /bin/bash -c "sudo -n systemctl status garage.service"
```

If the file doesn't exist, create it (see [Section 7](#7-configure-sudoers-for-deployments)).

### Health Check Fails After Deploy

**Symptoms:** The deploy log shows repeated "Health check attempt X/10 failed" followed by a rollback.

**Diagnosis:**

```bash
# Check service status
sudo systemctl status garage.service

# Check application logs
sudo journalctl -u garage.service -n 50 --no-pager

# Check the .env file exists and is readable
sudo ls -la /opt/garage/app/.env

# Try starting the app manually to see errors
sudo su - garage -s /bin/bash
cd /opt/garage/app
uv run python app.py
# Look for error messages, then Ctrl+C
exit
```

**Common causes:**

| Cause | Fix |
|-------|-----|
| Missing `.env` file | Recreate from `.env.example` — see `PRODUCTION.md` |
| Database not running | `sudo systemctl start mariadb` |
| Port 5000 already in use | `sudo lsof -i :5000` — kill the stale process |
| Python dependency issue | `cd /opt/garage/app && uv sync --frozen` |

### Runner Won't Register (Token Expired)

Registration tokens expire after **1 hour**. If you see "invalid token" errors:

**Web UI:** Go to **Settings** → **Actions** → **Runners** → **New self-hosted runner** — a new token is generated each time you visit this page.

**CLI:**

```bash
NEW_TOKEN=$(gh api repos/OWNER/REPO/actions/runners/registration-token --method POST --jq '.token')
echo "New token: $NEW_TOKEN"
```

Then re-run the `./config.sh` command with the new token.

### `git fetch` Fails

**Symptoms:** Deploy fails at "Fetching latest code from origin/main..."

```bash
# Check git remote URL
cd /opt/garage/app
git remote -v
# Should show your GitHub repository URL

# Test connectivity
git ls-remote origin main
# Should show the latest commit hash

# If using HTTPS and getting auth errors, configure a credential helper:
git config --global credential.helper store
# Then do a manual git pull once to cache credentials
```

### Rollback Happened — How to Investigate

If the deploy log shows `DEPLOY FAILED — ROLLED BACK`:

1. Check what commit was being deployed:
   ```bash
   grep "Deployed commit:" /opt/garage/deploy.log | tail -1
   ```

2. Check what error caused the failure:
   ```bash
   grep -A5 "ERROR\|CRITICAL\|failed" /opt/garage/deploy.log | tail -20
   ```

3. Review the application logs around the deploy time:
   ```bash
   sudo journalctl -u garage.service --since "10 minutes ago"
   ```

---

## 11. Runner Maintenance

### Updating the Runner to a Newer Version

GitHub periodically releases new runner versions. The runner will show a warning in logs when an update is available.

```bash
cd /opt/github-runner

# Stop the service
sudo ./svc.sh stop

# Download the new version (check releases page for latest URL)
LATEST=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name' | sed 's/^v//')
curl -o actions-runner-linux-arm64.tar.gz -L \
  "https://github.com/actions/runner/releases/download/v${LATEST}/actions-runner-linux-arm64-${LATEST}.tar.gz"

# Extract (overwrites existing files)
tar xzf actions-runner-linux-arm64.tar.gz

# Start the service again
sudo ./svc.sh start

# Verify
./run.sh --version
```

### Removing the Runner

If you need to decommission the runner:

**Option A — Web UI:**

1. Go to **Settings** → **Actions** → **Runners**
2. Click on `garage-pi-runner`
3. Click **Remove** (or the trash icon)
4. Confirm the removal

**Option B — CLI (on the Pi):**

```bash
cd /opt/github-runner

# Stop and uninstall the service
sudo ./svc.sh stop
sudo ./svc.sh uninstall

# Remove the runner registration
# You need a new removal token:
REMOVE_TOKEN=$(gh api repos/OWNER/REPO/actions/runners/remove-token --method POST --jq '.token')
./config.sh remove --token "$REMOVE_TOKEN"
```

**Option C — `gh` CLI (from anywhere):**

```bash
# List runners to find the ID
gh api repos/OWNER/REPO/actions/runners --jq '.runners[] | {id, name}'

# Remove by ID
gh api repos/OWNER/REPO/actions/runners/RUNNER_ID --method DELETE
```

### Viewing Runner Logs

```bash
# Live logs
journalctl -u actions.runner.*.service -f

# Last 100 lines
journalctl -u actions.runner.*.service -n 100 --no-pager

# Logs from today only
journalctl -u actions.runner.*.service --since today
```

### Monitoring Runner Status

**Web UI:** **Settings** → **Actions** → **Runners** — check the status dot (green = online, grey = offline).

**CLI:**

```bash
gh api repos/OWNER/REPO/actions/runners \
  --jq '.runners[] | "\(.name): \(.status) [\(.labels | map(.name) | join(", "))]"'
```

---

## Security Considerations

- **The runner runs as the `garage` user** — the same user that owns the application. This avoids file permission issues during deploys.
- **Sudoers is strictly scoped** — the `garage` user can only run four specific `systemctl` commands as root, nothing else.
- **The runner directory (`/opt/github-runner`) is separate from the app (`/opt/garage/app`)** — the runner's working files don't interfere with the application.
- **No inbound ports required** — the runner connects outbound to GitHub over HTTPS. Your Pi does not need to be exposed to the internet.
- **Registration tokens are single-use and expire** — each token is valid for 1 hour and can only register one runner.
- **Consider using a fine-grained Personal Access Token** or GitHub App for runner registration if you want tighter access control. See [GitHub's docs on runner authentication](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners).

---

## Quick Reference

| Task | Command |
|------|---------|
| Check runner status | `systemctl status actions.runner.*.service` |
| View runner logs | `journalctl -u actions.runner.*.service -f` |
| Restart runner | `cd /opt/github-runner && sudo ./svc.sh stop && sudo ./svc.sh start` |
| View deploy log | `cat /opt/garage/deploy.log` |
| Manual deploy | `cd /opt/garage/app && bash deploy.sh` |
| Check deployed commit | `cd /opt/garage/app && git log --oneline -1` |
| App health check | `curl -sf http://127.0.0.1:5000/login > /dev/null && echo OK` |
| Check runner on GitHub | **Settings** → **Actions** → **Runners** |
| View deploy runs | **Actions** tab → **Deploy to Raspberry Pi** |
