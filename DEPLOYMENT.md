# Deploy to Vercel + Render

## What you need

1. **GitHub account** – push your code to a GitHub repo
2. **Vercel account** – [vercel.com](https://vercel.com)
3. **Render account** – [render.com](https://render.com)
4. **Nothing else** – no Twilio, MQTT, or API keys required to get it running

---

## Step 1: Push code to GitHub

```powershell
cd c:\Users\Lqg\Desktop\Backend
git add .
git commit -m "Add deployment config"
git push origin main
```

---

## Step 2: Deploy backend on Render

1. Go to [render.com](https://render.com) → **Dashboard** → **New** → **Web Service**
2. Connect your GitHub repo and select the **Backend** repository
3. Render should auto-detect `render.yaml`. If not:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Click **Create Web Service**
5. Wait for the deploy to finish
6. Copy your backend URL, e.g. `https://medication-backend-xxxx.onrender.com`

---

## Step 3: Deploy frontend on Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project**
2. Import your GitHub repo
3. **Root Directory:** set to `Frontend` (important)
4. **Environment Variables** – add:

   | Name            | Value                                         |
   |-----------------|-----------------------------------------------|
   | `VITE_API_URL`  | `https://medication-backend-xxxx.onrender.com` |

   Use the backend URL from Step 2. No trailing slash.

5. Click **Deploy**

---

## Step 4: Allow frontend in CORS (Render)

1. In Render dashboard → your backend service → **Environment**
2. Add variable:
   - **Key:** `ALLOWED_ORIGINS`
   - **Value:** `https://your-app.vercel.app`
3. Redeploy the backend

---

## Notes

- **Render free tier:** Backend sleeps after ~15 min of inactivity. First request may take 30–60 seconds.
- **Data:** SQLite on Render is ephemeral; data can reset on redeploys. For production, use a managed PostgreSQL.
- **Twilio (optional):** Add `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` in Render for WhatsApp alerts.
