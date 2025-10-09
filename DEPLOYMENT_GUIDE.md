# 🚀 Smart Credit & Loan Manager - Render Deployment Guide

## 📋 Overview
This guide will help you deploy the CreditPilot Smart Credit & Loan Manager system to Render platform with full admin panel, email notifications, and WhatsApp alerts.

## ✅ Prerequisites
- GitHub account
- Render.com account (free tier available)
- Gmail account for email notifications (optional)
- Twilio account for WhatsApp notifications (optional)

## 🔧 Step 1: Push to GitHub

1. Create a new repository on GitHub (e.g., `creditpilot-smart-loan-manager`)

2. In Replit Shell, run:
```bash
git remote add origin https://github.com/YOUR_USERNAME/creditpilot-smart-loan-manager.git
git branch -M main
git add .
git commit -m "Initial deployment setup"
git push -u origin main
```

## 🌐 Step 2: Deploy to Render

### A. Create Web Service

1. Login to [Render.com](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure as follows:
   - **Name**: creditpilot-smart-loan-manager
   - **Region**: Singapore or Hong Kong
   - **Branch**: main
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
   - **Environment**: Python 3

### B. Set Environment Variables

Add the following environment variables in Render Dashboard:

#### Required Variables:
- `FLASK_ENV` = `production`
- `SESSION_SECRET` = (Generate a secure random string - min 32 characters)
- `ADMIN_EMAIL` = (Set your secure admin email)
- `ADMIN_PASSWORD` = (Set a strong password - min 12 characters with uppercase, lowercase, numbers, symbols)

#### Email Notifications (Optional):
- `EMAIL_USER` = your_email@gmail.com
- `EMAIL_PASSWORD` = your_app_specific_password
- `SMTP_SERVER` = smtp.gmail.com
- `SMTP_PORT` = 587

#### WhatsApp Notifications via Twilio (Optional):
- `TWILIO_ACCOUNT_SID` = your_twilio_account_sid
- `TWILIO_AUTH_TOKEN` = your_twilio_auth_token
- `TWILIO_WHATSAPP_FROM` = whatsapp:+14155238886
- `WHATSAPP_ADMIN_TO` = whatsapp:+60123456789

## 📧 Step 3: Setup Email (Gmail)

1. Go to Google Account Settings
2. Enable 2-Factor Authentication
3. Generate App-Specific Password:
   - Go to Security → App Passwords
   - Select "Mail" and your device
   - Copy the 16-character password
4. Use this password for `EMAIL_PASSWORD` in Render

## 📱 Step 4: Setup WhatsApp (Twilio)

1. Sign up at [Twilio.com](https://www.twilio.com)
2. Get your Account SID and Auth Token from Dashboard
3. Enable WhatsApp Sandbox:
   - Go to Messaging → Try it out → Send a WhatsApp message
   - Join sandbox by sending the code to +1 415 523 8886
4. Use sandbox number for `TWILIO_WHATSAPP_FROM`
5. Your WhatsApp number should be formatted as `whatsapp:+60123456789`

## 🎯 Step 5: Access Your Application

After deployment, you'll receive a URL like:
```
https://creditpilot-smart-loan-manager.onrender.com
```

### System Endpoints:

#### Public Access:
- 🏠 Homepage: `/`
- 📊 News: `/banking-news`
- 👤 Customer Login: `/customer/login`
- 👤 Customer Register: `/customer/register`

#### Admin Access:
- 🔐 Admin Login: `/admin-login`
  - Use credentials set in environment variables (ADMIN_EMAIL / ADMIN_PASSWORD)
- 📊 Admin Dashboard: `/admin`
- 📰 News Management: `/admin/news`

#### Customer Portal:
- 📤 Upload Statement: `/upload_statement`
- 📊 View Dashboard: `/customer/<id>`
- 💰 Loan Evaluation: `/loan-evaluation`
- 📈 Analytics: `/analytics`

## 🔔 Notification System

### Automatic Notifications:
1. **Statement Upload**: Admin receives email + WhatsApp when customer uploads statement
2. **Consultation Request**: Admin receives notification when customer requests consultation
3. **Payment Reminders**: System sends scheduled payment reminders

### Test Notifications:
- Upload a statement → Check admin WhatsApp/Email
- Request consultation → Verify notification received

## 🛡️ Security Notes

1. **Set Strong Admin Credentials**: 
   - Use a unique email address for ADMIN_EMAIL
   - Generate a strong password (min 12 chars: uppercase, lowercase, numbers, symbols)
   - NEVER use default or simple passwords like "Admin@2025"
   
2. **Secure Session Management**:
   - Generate a cryptographically secure SESSION_SECRET (min 32 random characters)
   - Rotate SESSION_SECRET periodically in production
   
3. **Environment Variables**:
   - Set all secrets ONLY in Render Dashboard (never commit to Git)
   - Use Render's sync: false for sensitive values
   
4. **HTTPS & SSL**: Render provides automatic SSL certificates

5. **Regular Security Audits**:
   - Review admin access logs regularly
   - Update dependencies periodically
   - Monitor for suspicious activity

## 📊 Features Enabled

✅ Admin login protection
✅ Graphical admin dashboard
✅ Email notifications (SMTP)
✅ WhatsApp alerts (Twilio)
✅ Customer authentication
✅ Statement processing
✅ Financial advisory
✅ Banking news system
✅ Budget management
✅ Automated scheduling

## 🔧 Production Deployment Configuration

The system uses:
- **Gunicorn** WSGI server (4 workers)
- **SQLite** database (auto-created on first run)
- **Scheduled tasks** for reminders and news fetching
- **Session-based authentication**

## 📝 Post-Deployment Checklist

- [ ] Test admin login at `/admin-login`
- [ ] Verify email notifications work
- [ ] Confirm WhatsApp alerts functional
- [ ] Test customer registration/login
- [ ] Upload test statement
- [ ] Check admin dashboard data
- [ ] Review banking news display
- [ ] Test all navigation links

## 🆘 Troubleshooting

### Issue: Email not sending
- Verify Gmail App Password is correct
- Check SMTP settings (port 587 for TLS)
- Ensure 2FA is enabled on Gmail

### Issue: WhatsApp not working
- Confirm Twilio sandbox is active
- Verify phone number format: `whatsapp:+60123456789`
- Check Twilio account balance

### Issue: Database errors
- Render may need to rebuild: redeploy the service
- Check logs in Render Dashboard

## 📞 Support

For issues or questions:
- Admin Email: admin@infinitegz.com
- System Status: Check Render Dashboard Logs

---

**Deployment Status**: ✅ Ready for Production
**Last Updated**: October 2025
**Version**: 2.0.0
