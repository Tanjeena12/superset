import os
import time
import requests

# 1. Configuration & Credentials
# Your working Personal API Key (apk_...) and GitHub Token (github_pat_...)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEVIN_API_KEY = os.getenv("DEVIN_API_KEY")
ORG_ID = os.getenv("DEVIN_ORG_ID")
REPO = "Tanjeena12/superset"

# In-memory database to track running sessions for the observability dashboard
active_sessions = []


def check_github_issues():
    url = f"https://api.github.com/repos/{REPO}/issues?labels=devin-fix&state=open"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    try:
        response = requests.get(url, headers=headers).json()
        return response
    except Exception as e:
        print(f"❌ Network error checking GitHub: {e}")
        return []


def remove_label_from_issue(issue_number):
    """Removes the trigger label so the script skips it on the next loop iteration"""
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}/labels/devin-fix"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    res = requests.delete(url, headers=headers)
    if res.status_code in [200, 204]:
        print(f"🏷️ Successfully removed 'devin-fix' label from Issue #{issue_number}")
    else:
        print(f"⚠️ Failed to remove label from Issue #{issue_number}: {res.text}")


def trigger_devin(issue_title, issue_body, issue_number):
    prompt = f"""
    You are an automated code remediation worker. 
    Your task is to fix Issue #{issue_number} in the repository: https://github.com/{REPO}

    Issue Title: {issue_title}
    Issue Description: {issue_body}

    Instructions:
    1. Clone the repository.
    2. Create a new branch named 'fix/issue-{issue_number}'.
    3. Remediate the issue described above.
    4. Run basic syntax checks to ensure it's not broken.
    5. Commit, push, and open a Pull Request back to the main branch of {REPO}.
    """

    url = "https://api.devin.ai/v1/sessions"
    headers = {
        "Authorization": f"Bearer {DEVIN_API_KEY.strip()}",
        "X-Devin-Organization": ORG_ID.strip(),
        "Content-Type": "application/json"
    }
    payload = {"prompt": prompt}

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code not in [200, 201]:
            print(f"❌ Devin API Error (Status {response.status_code}): {response.text}")
            return None
        return response.json().get("session_id")
    except Exception as e:
        print(f"❌ Failed to reach Devin API: {e}")
        return None


def check_devin_status(session_id):
    """Queries Devin v3 API to fetch real-time session updates for dashboard metrics"""
    url = f"https://api.devin.ai/v3/organizations/{ORG_ID.strip()}/sessions/{session_id}"
    headers = {"Authorization": f"Bearer {DEVIN_API_KEY.strip()}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Returns tuple: (status_string, pr_url_or_None)
            return data.get("status", "running"), data.get("pull_request", {}).get("url")
    except Exception:
        pass
    return "unknown", None


# --- Main Automation & Metrics Loop ---
print("🚀 Devin Automation Factory Initialized...")
while True:
    print("\nScanning repository for workspace triggers...")
    issues = check_github_issues()

    if isinstance(issues, list):
        for issue in issues:
            issue_num = issue['number']
            title = issue['title']
            print(f"🎯 Found target issue! Triggering Devin for: {title}")

            session_id = trigger_devin(title, issue['body'], issue_num)

            if session_id:
                print(f"🚀 Success! Agent workspace deployed.")
                # FIX INFINITE LOOP: Consume label immediately
                remove_label_from_issue(issue_num)

                # Append session info to our tracking index
                active_sessions.append({
                    "id": session_id,
                    "issue_num": issue_num,
                    "title": title
                })
    else:
        print("⚠️ Could not fetch clean issue list. Checking environment config.")

    # --- PART 3: OBSERVABILITY DASHBOARD PANEL ---
    if active_sessions:
        print("\n" + "=" * 50)
        print("📊 DEVIN AGENT FACTORY LEADERSHIP METRICS")
        print("=" * 50)
        print(f"Active Automations Running: {len(active_sessions)}")
        print("-" * 50)

        # Loop backwards through sessions so we can safely remove finished ones if needed
        for session in active_sessions[:]:
            status, pr_url = check_devin_status(session['id'])

            # Format emojis based on progress states
            status_emoji = "⚙️ RUNNING" if status == "running" else "✅ COMPLETED" if status == "completed" else "❌ FAILED" if status == "failed" else f"❓ {status.upper()}"

            print(f"[Session ID: {session['id']}]")
            print(f"Target Project : Issue #{session['issue_num']} - {session['title']}")
            print(f"Current Status : {status_emoji}")
            if pr_url:
                print(f"Pull Request   : {pr_url}")
            print("-" * 50)

    time.sleep(30)