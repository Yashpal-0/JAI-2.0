import json
import time
import urllib.request
import urllib.error

TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImVlYzIxN2Q0MThjYjhlNWEzMTQzMThhMGQyZmZhNGUwY2ViMmU0Y2MiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiWWFzaHBhbCBZYWRhdiAoWWFzaCkiLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSWxuaEhfWDlkTi12bC1KcmJuTDJpOUJOWEM4blQzTVhmcFVPWXZ2a3J4U0I3U1V3PXM5Ni1jIiwiaXNzIjoiaHR0cHM6Ly9zZWN1cmV0b2tlbi5nb29nbGUuY29tL3plcm9zdGljLWxsYyIsImF1ZCI6Inplcm9zdGljLWxsYyIsImF1dGhfdGltZSI6MTc3OTA1NzE1NiwidXNlcl9pZCI6IkZpdE9wdkNiSGZaMHZTZnd3VFNzUFp6NXoyRzIiLCJzdWIiOiJGaXRPcHZDYkhmWjB2U2Z3d1RTc1BaejV6MkcyIiwiaWF0IjoxNzc5MjQxMTk5LCJleHAiOjE3NzkyNDQ3OTksImVtYWlsIjoieWFzaHBhbHlhZGF2NTBAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMDcwOTg4NTk2NjI1MDUyMzEyMDUiXSwiZW1haWwiOlsieWFzaHBhbHlhZGF2NTBAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.aP7tt7NSveh5iYOXu0T0XXFVsuzmjOdnuQ82r8gTzhPr2GVEZTo-gZpv_7jDfUsbob5ydZr2QnrVStW2-fvCbeTaxAY0VufZnJwecxYZ4lzfi8YkK7LILcC0fjqPV-P2BAZoGiaKuOQlxjElRra5145qZ9RdMxUdzZUNkaxZpw8d9IXmNMiczReOVoJ6f06JXtiGwmX7MKGr4N8z9LZLWAOfSyF0ycPU5t_mvrfA58hXfskvEy7IizUZ0sEsDXkEVUDXQPjGDTjnIJBtUweCi7C6_OEyUDscMnKID6HKj55A98ER3CVjNsqFdV6sugHYUZ-FDRNPNfHhuHx-ERMDWQ"

URL = "https://studio.zerostic.com/api/jai/chat"

HEADERS = {
    "authorization": f"Bearer {TOKEN}",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0"
}

PROMPTS = [
    # Creation
    "Create a new project called Test",
    "Generate a logo for a coffee brand",
    "Make a social media post for Instagram",
    "Build a landing page for a SaaS product",
    "Design a banner with blue background",
    "Start a new Android app project",
    "Create a new iOS app project",
    "Create a static website",
    "Start a new custom software project",
    "Create a new ecommerce site",
    "Generate a branding package",
    "Start a new UI/UX design project",
    "Create a new marketing campaign project",
    "Build a new CRM project",
    "Make a new EdTech platform",
    "Create a new FinTech app",
    "Build a new HealthTech app",
    "Start a new gaming project",
    "Create a new AI/ML project",
    "Make a new blockchain project",
    "Start a new AR/VR project",
    "Create a new IoT project",
    "Build a new DevOps project",
    "Start a new QA project",
    "Create a new SEO project",

    # Navigation
    "Open my projects",
    "Go to settings",
    "Show me my recent files",
    "Take me to billing",
    "Open the template gallery",
    "Go to dashboard",
    "Open my profile",
    "Show me my contracts",
    "Take me to payments",
    "Open my invoices",
    "Show me my messages",
    "Take me to notifications",
    "Open my quotations",
    "Show me the scheduler",
    "Go to the help center",
    "Take me to contact support",
    "Open the API docs",
    "Show me my integrations",
    "Take me to webhooks",
    "Open the security settings",

    # Information
    "What plan am I on?",
    "How many projects do I have?",
    "What can you do?",
    "Tell me about Zerostic",
    "What are my API limits?",
    "Explain the AppLab feature",
    "Explain the FnO Bazar feature",
    "What is the LOA Mobile App?",
    "Tell me about mBuddy",
    "What is Good Morning - Everyday Alarm?",
    "What are the pricing tiers?",
    "How much does a static website cost?",
    "How much does an Android app cost?",
    "How much does an iOS app cost?",
    "Who is Jayant Jha?",
    "Where is Zerostic located?",
    "What is the company size?",
    "What is the company's mission?",
    "When was Zerostic founded?",
    "Who are Zerostic's partners?",

    # Edit / Action
    "Rename this project to X",
    "Delete the last file I uploaded",
    "Export this as PDF",
    "Publish this project",
    "Duplicate this project",
    "Change the settings for X",
    "Update my profile picture",
    "Change my email address",
    "Update my password",
    "Enable two-factor authentication",
    "Disable push notifications",
    "Mark all notifications as read",
    "Archive this project",
    "Restore this project",
    "Cancel my subscription",
    "Upgrade my plan",
    "Downgrade my plan",
    "Add a new payment method",
    "Remove a payment method",
    "Generate a new API key",
    "Revoke an API key",
    "Add a new team member",
    "Remove a team member",
    "Change a team member's role",

    # Zerostic Company Questions
    "Who made you?",
    "What is Zerostic?",
    "Tell me about the team",
    "What other products does Zerostic have?",
    "What's on the roadmap?",
    "What is the company's vision?",
    "What are the company values?",
    "How can I contact sales?",
    "Where can I find the press kit?",
    "Do you have a referral program?",

    # Edge Cases & Ambiguous
    "Help",
    "I need something done",
    "Make it better",
    "Do that thing again",
    "What about competitors like Vercel?",
    "How does Zerostic compare to agencies on Upwork?",
    "Can you write a poem?",
    "What is the meaning of life?",
    "ksadhfksjdfh",
    "rm -rf /",
    "Drop table users",
    "Select * from users",
    "Create a project and delete my account and send an email to everyone",
    "Change my password to 'password123' and upgrade my plan to enterprise",
    "I hate this product",
    "This is the best product ever",
]

# Ensure exactly 100 prompts (we have 91 currently, add 9 more)
PROMPTS.extend([
    "Show me my analytics",
    "Export my data",
    "Import data from CSV",
    "Connect to GitHub",
    "Connect to Slack",
    "Set up a webhook",
    "View audit logs",
    "Change timezone",
    "Change language to Spanish",
])

results = []

for idx, prompt in enumerate(PROMPTS):
    print(f"[{idx+1}/{len(PROMPTS)}] Testing: {prompt}")
    
    payload = {
        "message": prompt,
        "conversationId": f"-test-automation-{idx}",
        "context": {
            "client": {
                "name": "Yashpal Yadav (Yash)",
                "email": "yashpalyadav50@gmail.com",
                "verified": False
            },
            "projects": [],
            "payments": [],
            "invoices": [],
            "quotations": []
        },
        "history": []
    }
    
    start_time = time.time()
    try:
        req = urllib.request.Request(URL, data=json.dumps(payload).encode('utf-8'), headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            end_time = time.time()
            response_time = round(end_time - start_time, 2)
            status_code = response.getcode()
            response_body = response.read().decode('utf-8')
            
            data = json.loads(response_body)
            jai_response = data.get("data", {}).get("message", "NO_MESSAGE_FOUND")
            
            results.append({
                "intent": prompt,
                "response": jai_response,
                "response_time": response_time,
                "status": status_code,
                "api_call": {
                    "url": URL,
                    "method": "POST",
                    "payload": payload,
                    "response": data
                }
            })
    except urllib.error.HTTPError as e:
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        print(f"HTTPError testing prompt '{prompt}': {e.code}")
        results.append({
            "intent": prompt,
            "response": f"ERROR: HTTP {e.code} - {e.read().decode('utf-8')}",
            "response_time": response_time,
            "status": e.code,
            "api_call": None
        })
    except Exception as e:
        print(f"Error testing prompt '{prompt}': {e}")
        results.append({
            "intent": prompt,
            "response": f"EXCEPTION: {str(e)}",
            "response_time": 0,
            "status": 0,
            "api_call": None
        })

    time.sleep(0.5)

with open("jai_test_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Saved {len(results)} results to jai_test_results.json")
