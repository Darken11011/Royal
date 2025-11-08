# Deployment Guide - AI Voice Assistant

## 🚀 Deploy to Render.com (Recommended - Free)

### Prerequisites
- GitHub account
- Render.com account (free)
- Google Gemini API key

### Step 1: Prepare Your Repository

1. **Initialize Git** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit - AI Voice Assistant"
   ```

2. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git branch -M main
   git push -u origin main
   ```

   ⚠️ **Important**: Make sure `.env` is in `.gitignore` so your API key is NOT pushed to GitHub!

### Step 2: Deploy on Render

1. **Go to Render Dashboard**:
   - Visit: https://dashboard.render.com/
   - Sign up or log in

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository

3. **Configure Service**:
   - **Name**: `ai-voice-assistant` (or your choice)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

4. **Add Environment Variables**:
   - Click "Environment" tab
   - Add variable:
     - **Key**: `GEMINI_API_KEY`
     - **Value**: Your actual Gemini API key (from .env file)

5. **Deploy**:
   - Click "Create Web Service"
   - Wait 2-5 minutes for deployment
   - Your app will be live at: `https://your-app-name.onrender.com`

### Step 3: Access Your App

- **API Health Check**: `https://your-app-name.onrender.com/health`
- **Voice Assistant UI**: `https://your-app-name.onrender.com/app`

### Important Notes for Render Free Tier

⚠️ **Cold Starts**: Free tier spins down after 15 minutes of inactivity. First request after sleep takes ~30 seconds.

✅ **WebSocket Support**: Render free tier supports WebSockets (perfect for this app)

✅ **Auto-Deploy**: Pushes to GitHub automatically trigger redeployment

---

## 🚂 Alternative: Deploy to Railway.app

### Step 1: Deploy

1. Visit: https://railway.app/
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository

### Step 2: Configure

1. **Add Environment Variable**:
   - Go to "Variables" tab
   - Add: `GEMINI_API_KEY=your_api_key_here`

2. **Railway auto-detects Python** and uses:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Generate Domain**:
   - Go to "Settings" → "Generate Domain"
   - Your app will be live at: `https://your-app.up.railway.app`

### Railway Benefits
- ✅ No cold starts
- ✅ $5 free credit/month
- ✅ Better for real-time WebSocket apps

---

## 🛠️ Local Development

### Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file** (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

3. **Add your API key** to `.env`:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

4. **Run the server**:
   ```bash
   python main.py
   ```
   Or:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the app**:
   - API: http://localhost:8000
   - Voice UI: http://localhost:8000/app
   - Health: http://localhost:8000/health

---

## 🔒 Security Checklist

- ✅ API key moved to environment variables
- ✅ `.env` file in `.gitignore`
- ✅ `.env.example` provided (without real keys)
- ⚠️ Update CORS settings in production (currently allows all origins)

---

## 📝 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | - | Google Gemini API key |
| `PORT` | No | 8000 | Server port (auto-set by Render) |
| `HOST` | No | 0.0.0.0 | Server host |

---

## 🐛 Troubleshooting

### Issue: "GEMINI_API_KEY must be set"
**Solution**: Add the environment variable in Render dashboard or your `.env` file

### Issue: WebSocket connection fails
**Solution**: 
- Check if your hosting platform supports WebSockets
- Verify the WebSocket URL uses `wss://` (not `ws://`) for HTTPS sites

### Issue: Cold start delays on Render
**Solution**: 
- This is normal for free tier
- Consider upgrading to paid tier ($7/month) for always-on service
- Or use Railway.app which has no cold starts

### Issue: App crashes on startup
**Solution**: 
- Check logs in Render dashboard
- Verify all dependencies in `requirements.txt`
- Ensure Python version compatibility (3.11+)

---

## 📊 Monitoring

### Render Dashboard
- View logs: Dashboard → Your Service → Logs
- Monitor metrics: CPU, Memory, Request count
- Check health: `/health` endpoint

### Logs
```bash
# View logs in Render dashboard or use Render CLI
render logs -f
```

---

## 🔄 Updates & Redeployment

### Automatic (Recommended)
1. Push changes to GitHub
2. Render auto-deploys from `main` branch

### Manual
1. Go to Render dashboard
2. Click "Manual Deploy" → "Deploy latest commit"

---

## 💰 Cost Comparison

| Platform | Free Tier | Cold Starts | WebSockets | Best For |
|----------|-----------|-------------|------------|----------|
| **Render** | 750 hrs/mo | Yes (~30s) | ✅ Yes | Side projects |
| **Railway** | $5 credit/mo | No | ✅ Yes | Production apps |
| **Fly.io** | 3 VMs free | No | ✅ Yes | Global apps |
| **Koyeb** | 1 service | No | ✅ Yes | Simple apps |

---

## 🎉 Success!

Your AI Voice Assistant is now deployed and accessible worldwide! 

**Next Steps**:
- Share your app URL
- Monitor usage in dashboard
- Consider upgrading for production use
- Add custom domain (available on paid plans)

