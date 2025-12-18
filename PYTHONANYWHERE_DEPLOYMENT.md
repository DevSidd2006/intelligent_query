# PythonAnywhere Deployment Guide

This guide will help you deploy the Intelligent Query application to PythonAnywhere.

## Prerequisites

1. A PythonAnywhere account (free or paid)
2. Your OpenRouter API key
3. Basic familiarity with PythonAnywhere dashboard

## Step-by-Step Deployment

### 1. Upload Your Code

**Option A: Using Git (Recommended)**
```bash
# In PythonAnywhere console
cd ~
git clone https://github.com/yourusername/intelligent_query.git
cd intelligent_query
```

**Option B: Upload Files**
- Use PythonAnywhere's file manager to upload your project files
- Extract to `/home/yourusername/intelligent_query/`

### 2. Set Up Environment

Run the setup script in PythonAnywhere console:
```bash
cd ~/intelligent_query
python3.10 pythonanywhere_setup.py
```

### 3. Install Dependencies

```bash
# Use the PythonAnywhere optimized requirements
pip3.10 install --user -r requirements_pythonanywhere.txt
```

### 4. Configure Environment Variables

Edit the `.env` file:
```bash
nano .env
```

Update with your actual values:
```
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here
OPENROUTER_API_KEY=your-openrouter-api-key-here
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
```

### 5. Update WSGI Configuration

Edit `wsgi.py` and update the path:
```python
project_home = '/home/YOURUSERNAME/intelligent_query'  # Replace YOURUSERNAME
```

### 6. Configure Web App in PythonAnywhere Dashboard

1. Go to PythonAnywhere Dashboard → Web
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select Python 3.10
5. Set the following:

**Source code:** `/home/yourusername/intelligent_query`
**WSGI configuration file:** `/home/yourusername/intelligent_query/wsgi.py`

### 7. Configure Static Files (Optional)

If you have static files, add in the Static files section:
- URL: `/static/`
- Directory: `/home/yourusername/intelligent_query/src/static/`

### 8. Test the Setup

```bash
cd ~/intelligent_query
python3.10 test_setup.py
```

### 9. Reload and Test

1. Click "Reload" in your PythonAnywhere web app dashboard
2. Visit your app URL: `https://yourusername.pythonanywhere.com`

## Troubleshooting

### Common Issues

**Import Errors:**
- Check that all packages are installed: `pip3.10 list`
- Verify Python path in wsgi.py

**Memory Issues:**
- PythonAnywhere free accounts have memory limits
- Consider using smaller models or upgrading account

**File Upload Issues:**
- Check upload directory permissions
- Verify MAX_CONTENT_LENGTH setting

**API Key Issues:**
- Ensure .env file is properly configured
- Check that environment variables are loaded

### Debugging

Check error logs in PythonAnywhere:
1. Go to Web tab in dashboard
2. Click on "Error log" link
3. Check recent errors

### Performance Optimization

For better performance on PythonAnywhere:

1. **Use CPU-optimized models:**
   ```python
   # In your code, prefer smaller models
   model_name = "all-MiniLM-L6-v2"  # Smaller, faster model
   ```

2. **Optimize chunk sizes:**
   ```python
   # Reduce batch sizes for lower memory usage
   batch_size = 16  # Instead of 32
   ```

3. **Cache models:**
   ```python
   # Cache downloaded models to avoid re-downloading
   os.environ['TRANSFORMERS_CACHE'] = '/home/yourusername/.cache/transformers'
   ```

## Account Limits

**Free Account:**
- 512MB RAM
- 1GB disk space
- CPU seconds limit
- One web app

**Paid Account:**
- More RAM and disk space
- No CPU seconds limit
- Multiple web apps
- Better performance

## Security Notes

1. Never commit API keys to version control
2. Use strong SECRET_KEY
3. Keep dependencies updated
4. Monitor error logs regularly

## Support

If you encounter issues:
1. Check PythonAnywhere forums
2. Review error logs
3. Test locally first
4. Contact PythonAnywhere support for platform-specific issues

## File Structure on PythonAnywhere

```
/home/yourusername/intelligent_query/
├── wsgi.py                 # WSGI entry point
├── requirements_pythonanywhere.txt
├── .env                    # Environment variables
├── src/
│   ├── web_app.py         # Main Flask app
│   ├── app.py             # Core functionality
│   └── ...
├── uploads/               # File uploads
├── logs/                  # Application logs
└── temp/                  # Temporary files
```