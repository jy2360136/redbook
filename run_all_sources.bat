@echo off
chcp 65001 >nul
echo ==================================================
echo 🚀 金融新闻自动化工作流 - 4 大权威媒体
echo ==================================================
echo 开始时间：%date% %time%
echo.

python financial_news_workflow_crawl4ai.py --days 10 --sources huxiu,36kr,tmtpost,jiemian

echo.
echo 完成时间：%date% %time%
echo ==================================================
pause
