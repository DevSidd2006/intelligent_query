# PythonAnywhere Deployment Checklist

## Pre-Deployment

- [ ] Have PythonAnywhere account ready
- [ ] Have OpenRouter API key
- [ ] Code is working locally
- [ ] All files are uploaded to PythonAnywhere

## Deployment Steps

### 1. File Setup
- [ ] Upload project to `/home/yourusername/intelligent_query/`
- [ ] Run `python3.10 pythonanywhere_setup.py`
- [ ] Install packages: `pip3.10 install --user -r requirements_pythonanywhere.txt`

### 2. Configuration
- [ ] Update `.env` file with real API keys
- [ ] Update `wsgi.py` with your username path
- [ ] Test setup: `python3.10 test_setup.py`

### 3. PythonAnywhere Dashboard
- [ ] Create new web app (Manual configuration, Python 3.10)
- [ ] Set source code path: `/home/yourusername/intelligent_query`
- [ ] Set WSGI file: `/home/yourusername/intelligent_query/wsgi.py`
- [ ] Click "Reload" button

### 4. Testing
- [ ] Visit your app URL
- [ ] Test file upload
- [ ] Test query functionality
- [ ] Check error logs if issues

## Common Issues & Solutions

**Import Errors:**
```bash
# Check Python path in console
python3.10 -c "import sys; print(sys.path)"
```

**Package Issues:**
```bash
# List installed packages
pip3.10 list | grep -i flask
pip3.10 list | grep -i torch
```

**Memory Issues:**
- Use smaller models in production
- Reduce batch sizes
- Consider upgrading PythonAnywhere account

## Files Created for Deployment

1. `wsgi.py` - WSGI entry point
2. `requirements_pythonanywhere.txt` - Optimized dependencies
3. `pythonanywhere_setup.py` - Setup script
4. `test_setup.py` - Test script (created by setup)
5. `.env` - Environment variables (created by setup)

## Support Resources

- PythonAnywhere Help: https://help.pythonanywhere.com/
- Flask on PythonAnywhere: https://help.pythonanywhere.com/pages/Flask/
- Forums: https://www.pythonanywhere.com/forums/