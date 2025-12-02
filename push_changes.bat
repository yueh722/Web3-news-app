@echo off
REM 設定 Git 自動轉換換行符號
git config --global core.autocrlf true

REM 進入你的專案資料夾（可修改成實際路徑）
cd /d C:\Work_n8n\Daily_news\NewsCommentApp

REM 將所有修改加入暫存區
git add .

REM 提交，接受使用者輸入提交訊息
set /p msg=Enter commit message: 
git commit -m "%msg%"

REM 推送到遠端 main 分支
git push origin main

echo.
echo Push completed!
pause
