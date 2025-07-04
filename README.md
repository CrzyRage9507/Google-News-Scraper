# Google-News-Scraper

The script is a easy to use, keep updated tool that automates searching Google for specific keywords and saves the findings into a nicely formatted Excel file.

The tool's still in its early stages (version 1.0), due to limited programming skills, I developed this tool with the assistance of AI;
Currently, the tool mainly uses RSS sources, supplemented by HTML sources, to crawl news;

**Excel spreadsheet included: title, link, publish_time, query, is_recent_24h, scraped_at**

*该脚本是一个简单易用、持续更新的工具，可以自动在 Google 上搜索特定关键字，并将搜索结果保存到的 Excel 文件格式中。该工具尚处于早期阶段（1.0 版），由于编程能力有限，我借助人工智能技术开发了此工具；目前，该工具主要使用 RSS 源，以 HTML 源为辅，进行新闻爬取。*

**Prerequisites**: Python 3.13

### Installation:

```pip install requests beautifulsoup4 pandas openpyxl```

### Get Prepared
1. Modify the **keywords** in the main() function
2. Set your preferred **output directory**


### Usage:

**1) Changed Export Location**

Default location: Saves to Desktop.

Customizable: You can change the output directory by modifying the  variable in the  functionoutput_directorymain()

Here are some examples for different locations:
```
python# Save to Desktop (default)

output_directory = None

output_directory = "C:/Downloads"

output_directory = "D:/MyNewsData"
```

**2) How to Change Keywords**

In the  function, look for this section:main()
```
python# 1. CHANGE KEYWORDS HERE:
# Replace the keywords below with your desired search terms
keywords = ["Student", "University", "College"]
```

**3) Start Scraping
1. Open 'start_py_scraper -v2.bat', change the location where you put 'sharing_scraper_version.py'. After you done it, save it.

2. click the 'start_py_scraper -v2.bat' file and run.

### Q&A/Notes

### How many articles can I fetch with this scraper? 
*使用此工具可以抓取多少篇文章？*

Support to get hundreds of results instead of just 30-40, max_html_pages 8-10.

*可获取数百个结果，而非仅限于30-40个，最多可收集8-10页。*


### **DISCLAIMER:**

This script is for educational purposes only. Users are responsible for complying with applicable laws and website terms of service.
