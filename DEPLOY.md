# Deployment Instructions

## 1. Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Dating App MVP"

# Create GitHub repository and push
git remote add origin https://github.com/YOUR_USERNAME/dating-app.git
git branch -M main
git push -u origin main
```

## 2. Deploy to Render

### Option A: Using render.yaml (Recommended)

1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and create:
   - Web service
   - PostgreSQL database
5. Click "Apply"
6. Wait for deployment (2-3 minutes)

### Option B: Manual Setup

1. Go to [render.com](https://render.com)
2. Click "New +" → "PostgreSQL"
   - Name: `dating-db`
   - Plan: Free
   - Create Database
3. Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Name: `dating-app`
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers 4 run:app`
4. Add Environment Variables:
   - `DATABASE_URL`: (copy from PostgreSQL service)
   - `SECRET_KEY`: (generate random string)
5. Click "Create Web Service"

## 3. Get Live URL

After deployment:
- Your app will be at: `https://dating-app-XXXX.onrender.com`
- Find the exact URL in your Render dashboard

## 4. First Time Setup

Visit your live URL and:
1. Register a new account
2. Complete your profile
3. Start using the app!

## Troubleshooting

### Database Connection Issues
```bash
# Check if tables were created
# In Render dashboard, go to PostgreSQL → Shell
psql $DATABASE_URL -c "\dt"
```

### View Logs
```bash
# In Render dashboard, go to your web service → Logs
```

### Restart Service
```bash
# In Render dashboard, click "Manual Deploy" → "Deploy latest commit"
```
