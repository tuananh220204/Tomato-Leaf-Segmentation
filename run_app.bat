@echo off
setlocal
cd /d "%~dp0"

:: Thiết lập bảng mã UTF-8 để hiển thị tiếng Việt không bị lỗi font
chcp 65001 >nul

echo ===================================================
echo   KHOI DONG TOAN BO HE THONG TOMATO LEAF SEGMENTATION
echo ===================================================
echo.

:: 1. Khởi động mạng Blockchain (Mở cửa sổ CMD riêng, giữ nguyên)
echo [1/3] Đang khởi động mạng Blockchain (Hardhat)...
start "Hardhat Node" cmd /k "cd webapp && npm run node"

:: Đợi 5 giây để mạng Hardhat khởi động hoàn tất
timeout /t 5 /nobreak >nul

:: 2. Triển khai Smart Contract lên mạng local (Chạy xong tự đóng cửa sổ)
echo [2/3] Đang triển khai Hợp đồng thông minh SmartFarm...
start "Deploy Contract" cmd /c "cd webapp && npm run deploy:localhost"

:: Đợi 3 giây để tệp ABI được ghi đè vào frontend
timeout /t 3 /nobreak >nul

:: 3. Khởi động AI Backend (Chuyển vào thư mục backend và gọi .venv từ thư mục gốc)
echo [3/3] Đang khởi động AI Backend Server...
if exist ".venv\Scripts\python.exe" (
    start "AI Backend Server" cmd /k "cd webapp\backend && ..\..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000"
) else (
    echo [LỖI] Không tìm thấy .venv\Scripts\python.exe tại thư mục gốc!
    pause
    exit /b
)

echo.
echo ===================================================
echo   ✅ HỆ THỐNG ĐÃ SẴN SÀNG!
echo   - Mạng Blockchain đang chạy.
echo   - AI Backend đang lắng nghe ở cổng 8000.
echo   - Hãy mở file: webapp\frontend\index.html bằng trình duyệt.
echo ===================================================
pause