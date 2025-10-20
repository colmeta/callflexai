# 🦷 Dentist Chatbot Lead Generation - Complete Setup Guide

This guide will help you scrape 100+ dentists per day and send them personalized emails about your chatbot.

---

## 📋 Step 1: Setup Your Database (Supabase)

1. **Go to Supabase**: https://supabase.com
2. **Create a new project** (free tier is fine)
3. **Run the SQL schema**:
   - Click on "SQL Editor" in the left sidebar
   - Copy the entire content from `dentist_database_schema.sql`
   - Paste it and click "Run"
   - You should see: `dentists` table and `outreach_queue` table created

4. **Get your credentials**:
   - Go to Settings → API
   - Copy `Project URL` (save as `SUPABASE_URL`)
   - Copy `service_role` key (save as `SUPABASE_SERVICE_KEY`)

---

## 🔑 Step 2: Get API Keys

### SerpAPI (For Google Maps scraping)
1. Go to: https://serpapi.com/
2. Sign up (free tier: 100 searches/month)
3. Copy your API key
4. Save as `SERPAPI_API_KEY`

### Brevo (For sending emails)
1. Go to: https://www.brevo.com/
2. Sign up (free tier: 300 emails/day)
3. Go to Settings → SMTP & API
4. Create new API key
5. Save as `BREVO_API_KEY`

6. **Verify your sender email**:
   - Go to Senders → Add a Sender
   - Add your email (e.g., you@yourdomain.com)
   - Verify it via the email they send
   - Save as `FROM_EMAIL`

---

## 🛠️ Step 3: Setup Your Local Environment

1. **Create `.env` file** in your project root:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here

# SerpAPI (for scraping dentists)
SERPAPI_API_KEY=your-serpapi-key-here

# Brevo (for sending emails)
BREVO_API_KEY=your-brevo-key-here
FROM_EMAIL=you@yourdomain.com
FROM_NAME=Your Name
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

---

## 🚀 Step 4: Run Your First Scrape (Local Test)

### Test 1: Scrape Dentists
```bash
python dentist_scraper.py 20
```

This will:
- Scrape 20 dentists from major US cities
- Save to `dentists_scraped.csv`
- Save to Supabase `dentists` table

**Expected output**:
```
🦷 DENTIST SCRAPER: Target 20 dentists
🔍 Scraping dentists in New York, NY...
  ✅ Smile Dental NYC | Score: 8/10
  ✅ Downtown Dentistry | Score: 7/10
...
✅ Found 20 dentists
💾 DATABASE: Saved 20, Duplicates 0
```

### Test 2: Generate Emails
```bash
python email_generator.py
```

This will:
- Read dentists from database
- Generate personalized emails
- Save to `outreach_queue` table

**Expected output**:
```
📧 EMAIL GENERATOR: Starting...
✅ Found 20 dentists ready for outreach
  ✅ Generated for Smile Dental NYC
  ✅ Generated for Downtown Dentistry
...
📊 RESULTS: Generated: 20, Skipped: 0
```

### Test 3: Preview Emails (Test Mode)
```bash
python send_emails.py
```

This shows emails **WITHOUT sending** (safe):
```
🧪 TEST MODE: Showing first 3 emails (not sending)
EMAIL #1: Smile Dental NYC
To: info@smiledental.com
Subject: Quick question about Smile Dental NYC's patient scheduling
...
```

### Test 4: Send Emails (Live Mode)
```bash
python send_emails.py --live
```

This **actually sends** emails:
```
📧 EMAIL SENDER: LIVE MODE
📤 Sending 20 emails...
[1/20] Sending to Smile Dental NYC...
  ✅ Sent to Smile Dental NYC (info@smiledental.com)
...
📊 RESULTS: ✅ Sent: 20, ❌ Failed: 0
```

---

## 🤖 Step 5: Setup GitHub Actions (Automated Daily Scraping)

1. **Add secrets to GitHub**:
   - Go to your repository
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Add all your keys:
     - `SUPABASE_URL`
     - `SUPABASE_SERVICE_KEY`
     - `SERPAPI_API_KEY`
     - `BREVO_API_KEY`
     - `FROM_EMAIL`
     - `FROM_NAME`

2. **Push the workflow file**:
```bash
git add .github/workflows/daily-dentist-scraper.yml
git commit -m "Add daily dentist scraper"
git push
```

3. **Test the workflow**:
   - Go to Actions tab
   - Click "Daily Dentist Scraper & Email Sender"
   - Click "Run workflow"
   - Wait ~5 minutes

4. **Check results**:
   - Go to Supabase → Table Editor → `dentists`
   - You should see 100 new dentists!
   - Go to `outreach_queue` → See generated emails
   - Check your Brevo dashboard for sent emails

---

## 📊 Step 6: Monitor Your Results

### View Dentists in Database
```sql
-- Top prospects (highest chatbot need)
SELECT business_name, city, state, needs_chatbot_score, contact_email
FROM dentists
WHERE status = 'new'
ORDER BY needs_chatbot_score DESC
LIMIT 20;
```

### View Sent Emails
```sql
-- Emails sent today
SELECT recipient_name, recipient_email, sent_at, status
FROM outreach_queue
WHERE sent_at::date = CURRENT_DATE
ORDER BY sent_at DESC;
```

### View Response Rate
```sql
-- How many dentists opened/replied
SELECT 
  status,
  COUNT(*) as count
FROM outreach_queue
GROUP BY status;
```

---

## 🎯 Expected Daily Results

**With GitHub Actions running daily**:
- ✅ 100 dentists scraped per day
- ✅ 50 emails sent per day (Brevo free limit is 300/day, but we're conservative)
- ✅ Fully automated (no manual work needed)

**After 1 week**:
- 700 dentists in database
- 350 emails sent
- Expected responses: 5-15 (1-4% response rate is normal)

**After 1 month**:
- 3,000 dentists in database
- 1,500 emails sent
- Expected interested prospects: 20-60
- Potential customers: 5-15

---

## 💰 Cost Breakdown

| Service | Plan | Cost | What You Get |
|---------|------|------|--------------|
| Supabase | Free | $0/month | 500MB database, 2GB bandwidth |
| SerpAPI | Free | $0/month | 100 searches/month (1 per city) |
| Brevo | Free | $0/month | 300 emails/day |
| GitHub Actions | Free | $0/month | 2,000 minutes/month |
| **TOTAL** | | **$0/month** | Fully automated lead gen! |

---

## 🔧 Customization Options

### Change target number of dentists
```bash
python dentist_scraper.py 200  # Scrape 200 instead of 100
```

### Change email sending limit
```bash
python send_emails.py --live 100  # Send 100 emails instead of 50
```

### Add more cities
Edit `dentist_scraper.py`, add to `USA_CITIES` list:
```python
USA_CITIES = [
    {'city': 'Your City', 'state': 'XX'},
    # ... more cities
]
```

### Customize email templates
Edit `email_generator.py`, modify the templates:
- `high_urgency_template()` - For high-score dentists
- `medium_urgency_template()` - For medium-score dentists
- `standard_template()` - For all others

---

## 🐛 Troubleshooting

### "No dentists found"
- Check SerpAPI key is correct
- Check you have API credits left
- Try a different city

### "Email sending failed"
- Check Brevo API key
- Verify your sender email in Brevo dashboard
- Check you haven't hit daily limit (300/day)

### "Database connection failed"
- Check Supabase URL and key
- Make sure you ran the SQL schema
- Check Supabase project is active

### GitHub Actions not running
- Check secrets are added correctly
- Look at Actions → Failed runs → View logs
- Make sure workflow file is in `.github/workflows/`

---

## 📈 Next Steps

Once you have dentists responding:

1. **Track conversations** - Add a `conversations` table in Supabase
2. **A/B test emails** - Try different subject lines
3. **Add follow-ups** - Send a 2nd email after 3 days if no response
4. **Scale up** - Upgrade SerpAPI to scrape 1,000/day
5. **Add phone calling** - Use Twilio to call hot leads

---

## 🎉 You're Ready!

Run this command to start everything:
```bash
python dentist_scraper.py 100 && python email_generator.py && python send_emails.py --live 50
```

Or just push to GitHub and let Actions handle it automatically every day!

Good luck with your chatbot sales! 🚀
