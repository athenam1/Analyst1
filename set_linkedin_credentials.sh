#!/bin/bash

# Script to set LinkedIn credentials as environment variables
# Usage: source set_linkedin_credentials.sh

echo "Setting LinkedIn credentials..."
echo ""

# You can set these here or export them in your shell
export LINKEDIN_EMAIL="your-email@example.com"
export LINKEDIN_PASSWORD="your-password"

echo "Credentials set! Now run: python app.py"
echo ""
echo "Or to set them manually, run:"
echo "  export LINKEDIN_EMAIL='your-email@example.com'"
echo "  export LINKEDIN_PASSWORD='your-password'"

