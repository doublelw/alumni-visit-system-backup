@echo off
REM Generate Secret Keys
REM Usage: Double click to generate keys

echo ============================================================
echo Generate Secret Keys for Deployment
echo ============================================================
echo.

echo [1/4] Generating SECRET_KEY...
openssl rand -base64 32
echo.

echo [2/4] Generating JWT_SECRET_KEY...
openssl rand -base64 32
echo.

echo [3/4] Generating ELECTRONIC_CARD_SECRET_KEY...
openssl rand -base64 32
echo.

echo [4/4] Generating HMAC_SECRET_KEY...
openssl rand -base64 32
echo.

echo ============================================================
echo Copy the keys above to your environment variables
echo ============================================================
echo.
pause
