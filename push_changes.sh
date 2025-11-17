#!/bin/bash

# Script to push README and LICENSE changes to GitHub

echo "🚀 Pushing changes to GitHub..."
echo ""

# Navigate to Analyst1 directory
cd /Users/athenacao/Analyst1

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Git repository not initialized."
    echo "Initializing git repository..."
    git init
    git remote add origin https://github.com/athenam1/Analyst1.git 2>/dev/null || git remote set-url origin https://github.com/athenam1/Analyst1.git
    echo "✅ Git repository initialized and remote added."
    echo ""
fi

# Check git status
echo "📋 Current git status:"
git status
echo ""

# Add the changed files
echo "➕ Adding README.md and LICENSE..."
git add README.md LICENSE

# Commit the changes
echo "💾 Committing changes..."
git commit -m "Add LICENSE and improve README for GitHub"

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push origin main

# Check if push was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed changes to GitHub!"
    echo "🌐 View your repository at: https://github.com/athenam1/Analyst1"
else
    echo ""
    echo "⚠️  Push failed. You may need to:"
    echo "   1. Set up authentication (SSH key or GitHub CLI)"
    echo "   2. Check your internet connection"
    echo "   3. Verify the remote URL is correct"
fi

