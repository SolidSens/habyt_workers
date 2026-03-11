import os
import json
from pathlib import Path
from dotenv import load_dotenv

def debug():
    print("--- Diagnostic Report ---")
    cwd = os.getcwd()
    print(f"Current Working Directory: {cwd}")
    
    script_dir = Path(__file__).parent.absolute()
    print(f"Script Directory: {script_dir}")
    
    env_path = script_dir / '.env'
    print(f"Target .env Path: {env_path}")
    print(f".env exists: {env_path.exists()}")
    
    if env_path.exists():
        print(f".env Size: {env_path.stat().st_size} bytes")
        # Check for BOM
        with open(env_path, 'rb') as f:
            head = f.read(4)
            print(f".env Head (Hex): {head.hex()}")
            
        load_dotenv(dotenv_path=env_path)
    
    vars_to_check = ['TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID', 'GMAIL_CREDENTIALS_PATH', 'GMAIL_TOKEN_PATH']
    for var in vars_to_check:
        val = os.getenv(var)
        print(f"{var}: {'[SET]' if val else '[NOT SET]'} (Length: {len(val) if val else 0})")
        if val:
            print(f"  Value (first/last 3): {val[:3]}...{val[-3:]}")

    json_files = ['credentials.json', 'token.json']
    for jf in json_files:
        jp = script_dir / jf
        print(f"\nTesting {jf}:")
        print(f"  Path: {jp}")
        print(f"  Exists: {jp.exists()}")
        if jp.exists():
            print(f"  Size: {jp.stat().st_size} bytes")
            try:
                with open(jp, 'r') as f:
                    data = json.load(f)
                    print(f"  JSON Load: SUCCESS (Keys: {list(data.keys())})")
            except Exception as e:
                print(f"  JSON Load: FAILED - {e}")

if __name__ == "__main__":
    debug()
