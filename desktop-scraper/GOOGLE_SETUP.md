# Google Cloud Console Setup Guide

This guide will help you set up Google OAuth credentials for the Local Web Scraper application.

## Prerequisites

- Google account
- Access to Google Cloud Console

## Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter project name: `local-web-scraper` (or your preferred name)
5. Click "Create"

### 2. Enable Required APIs

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for and enable the following APIs:
   - **Google Sheets API**
   - **Google Drive API**
   - **Google OAuth2 API** (usually enabled by default)

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" (unless you have a Google Workspace account)
   - Fill in the required fields:
     - App name: `Local Web Scraper`
     - User support email: Your email
     - Developer contact information: Your email
   - Add scopes:
     - `https://www.googleapis.com/auth/spreadsheets`
     - `https://www.googleapis.com/auth/drive.file`
     - `https://www.googleapis.com/auth/userinfo.profile`
     - `https://www.googleapis.com/auth/userinfo.email`
4. Back in Credentials, create OAuth client ID:
   - Application type: **Desktop application**
   - Name: `Local Web Scraper Desktop`
   - Click "Create"

### 4. Download Credentials

1. Click the download button next to your OAuth client
2. Save the JSON file securely
3. Copy the `client_id` and `client_secret` from the JSON file

### 5. Configure Application

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file with your credentials:
   ```env
   GOOGLE_CLIENT_ID=your-actual-client-id.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-actual-client-secret
   ```

### 6. Test Authentication

1. Start the application:
   ```bash
   npm run dev
   ```

2. Run through the setup wizard
3. Test Google authentication
4. Verify you can create and access Google Sheets

## Troubleshooting

### Common Issues

1. **"Error 400: redirect_uri_mismatch"**
   - Make sure your redirect URI in Google Cloud Console matches exactly: `http://localhost:8080/auth/callback`

2. **"This app isn't verified"**
   - Click "Advanced" > "Go to Local Web Scraper (unsafe)"
   - This is normal for development apps

3. **"Access denied"**
   - Make sure you've enabled all required APIs
   - Check that your OAuth consent screen is properly configured

4. **Invalid client error**
   - Double-check your client ID and secret in the `.env` file
   - Ensure there are no extra spaces or characters

### Development vs Production

- **Development**: You can use the same credentials locally
- **Production**: You'll need to verify your app with Google for public release

## Security Notes

- Never commit your `.env` file to version control
- Keep your `client_secret` secure
- For production apps, consider using environment variables or secure secret management
- Regularly rotate your credentials if compromised

## Scopes Explained

The application requests these permissions:

- **spreadsheets**: Create, read, and edit Google Sheets
- **drive.file**: Create and access files created by the app
- **userinfo.profile**: Get basic profile information (name, picture)
- **userinfo.email**: Get user's email address

These are the minimum required scopes for the application to function properly.