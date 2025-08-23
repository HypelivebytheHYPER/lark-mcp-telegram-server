#!/usr/bin/env python3
"""
Deploy the FastAPI server to Render using Git deployment
"""
import os
import subprocess
import sys

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return False, result.stderr
        return True, result.stdout
    except Exception as e:
        print(f"❌ Exception running command: {e}")
        return False, str(e)

def main():
    print("🚀 Deploying Lark-Telegram Bridge to Render...")
    
    # Check if we're in a git repository
    success, output = run_command("git status")
    if not success:
        print("📂 Initializing git repository...")
        run_command("git init")
        run_command("git add .")
        run_command('git commit -m "Initial production deployment"')
    
    # Create GitHub repository
    print("🔗 Creating GitHub repository...")
    success, output = run_command('gh repo create lark-bridge-production --public --description "Lark-Telegram Bridge Production Server"')
    if success:
        print("✅ GitHub repository created")
    else:
        print("⚠️ Repository might already exist, continuing...")
    
    # Push to GitHub
    print("📤 Pushing to GitHub...")
    run_command("git remote add origin https://github.com/HypelivebytheHYPE/lark-bridge-production.git")
    run_command("git branch -M main")
    success, output = run_command("git push -u origin main")
    
    if success:
        print("✅ Code pushed to GitHub successfully")
        print("📋 Repository URL: https://github.com/HypelivebytheHYPE/lark-bridge-production")
        print("\n🎯 Next steps:")
        print("1. Go to render.com")
        print("2. Create new Web Service") 
        print("3. Connect to GitHub repo: lark-bridge-production")
        print("4. Use these settings:")
        print("   - Build Command: pip install -r requirements.txt")
        print("   - Start Command: python app.py")
        print("   - Environment: Python")
        print("   - Plan: Starter")
        print("   - Environment Variables:")
        print("     PORT=10000")
        print("     RENDER=production")
    else:
        print(f"❌ Failed to push to GitHub: {output}")

if __name__ == "__main__":
    main()