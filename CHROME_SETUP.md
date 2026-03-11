# Chrome Setup Guide

## Problem: "Cannot connect to chrome at 127.0.0.1:9222"

This error occurs when the worker is configured to use **Remote Debugging Mode** but Chrome is not running with remote debugging enabled.

## Solution Options

### Option 1: Use Remote Debugging Mode (Recommended)

This allows the worker to connect to an existing Chrome instance that you can see and interact with.

#### Windows:
1. **Method A: Use the provided script**
   ```bash
   start_chrome_debug.bat
   ```

2. **Method B: Manual command**
   ```bash
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
   ```

#### macOS/Linux:
1. **Method A: Use the provided script**
   ```bash
   chmod +x start_chrome_debug.sh
   ./start_chrome_debug.sh
   ```

2. **Method B: Manual command**
   ```bash
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
   ```

**Important:** Keep Chrome running while the worker is active!

### Option 2: Use Local Profile Mode

If you prefer the worker to launch its own Chrome instance:

1. **Edit your `.env` file:**
   - Remove or comment out: `CHROME_DEBUG_PORT=9222`
   - Make sure `CHROME_USER_DATA_DIR` is set correctly
   - Make sure `CHROME_BINARY_PATH` is set correctly

2. **Example `.env` configuration:**
   ```env
   # Comment out or remove this line:
   # CHROME_DEBUG_PORT=9222
   
   # Make sure these are set:
   CHROME_USER_DATA_DIR="/Users/yourname/Library/Application Support/Google/Chrome"
   CHROME_PROFILE_NAME=Default
   CHROME_BINARY_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
   ```

**Note:** In local profile mode, you cannot have Chrome open with the same profile while the worker runs.

## Verifying the Setup

After starting Chrome with remote debugging, verify it's working:

1. Open: `http://localhost:9222/json` in your browser
2. You should see a JSON response with Chrome tabs information

If you see the JSON, Chrome is ready for the worker to connect!

## Troubleshooting

### Port 9222 already in use
- Another Chrome instance might already be using port 9222
- Close all Chrome windows and try again
- Or use a different port (update `.env` and the start command)

### Chrome path not found
- Find your Chrome installation:
  - **Windows:** Usually in `C:\Program Files\Google\Chrome\Application\chrome.exe`
  - **macOS:** Usually in `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- Update the script or command with the correct path

### Still having issues?
- Check the worker logs for detailed error messages
- Make sure your `.env` file has the correct paths
- Try Option 2 (Local Profile Mode) if remote debugging continues to fail
