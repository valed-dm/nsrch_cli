# Advanced Web Scraper & CAPTCHA Analysis Toolkit

![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg) 
![Playwright Automated](https://img.shields.io/badge/Playwright-Automated-green.svg) 
![curl_cffi Impersonated](https://img.shields.io/badge/curl_cffi-Impersonated-blueviolet.svg) 
![CLI Typer](https://img.shields.io/badge/CLI-Typer-brightgreen.svg) 
![Ollama AI](https://img.shields.io/badge/Ollama-AI-FF6B00.svg) 
![AI Assistant](https://img.shields.io/badge/AI-Assistant-00AAFF.svg) 
![License MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

# Mobile Emulation Scraper Toolkit

This project is a sophisticated **Python-based toolkit** designed to emulate mobile devices 
for automated web scraping on major search engines like **Google** and **Yandex**.  

It features a robust, multi-layered architecture focused on intelligently handling **anti-bot measures**,
including a complete workflow for detecting, collecting, and analyzing **CAPTCHAs**.

---

## 🔑 Key Features

### 📱 Advanced Mobile Emulation
- Utilizes **custom, rotating mobile device profiles** (Android/iOS)  
- Matching **user agents**, **screen resolutions**, and **dynamic timezones** derived from geolocation data  
- Produces a coherent and believable **browser fingerprint**  

### ⚡ Hybrid Scraping Strategy
- Fast, efficient primary method using **curl_cffi with TLS impersonation**  
- Leverages a **pre-warmed browser state** from a headless **Playwright** session  

### 🔒 Robust CAPTCHA Handling
- **Automatically detects** CAPTCHA pages  
- Falls back to a slower, **fully browser-based workflow** for complex multi-step challenges  
- Handles cookie banners and interactive forms seamlessly  

### 🌍 Intelligent Proxy Management
- Integrates a **rated proxy handler**:
  - Fetches a list of free proxies  
  - Tests them in **parallel** for latency & success  
  - Scores and ranks them  
- Uses the **best-ranked proxy** for critical tasks  
- Rotates through other high-quality proxies for subsequent actions  

### 🧩 Deterministic Parsing
- Uses **BeautifulSoup** with precise CSS selectors  
- Ensures **lightning-fast** and **highly reliable parsing** of search result pages  
- Outperforms AI-based parsing for structured tasks  

---

## 🛠️ Autonomous Reconnaissance Tools

### 🌙 Nightly CAPTCHA Collector
- Autonomous script designed for **long-term runs**  
- Uses a **diverse pool of low-quality proxies**  
- Intentionally triggers and collects **unique CAPTCHA pages**  

### 🧪 CAPTCHA Anatomy Analyzer
- Processes collected CAPTCHA pages  
- Uses **deterministic parsing** + local AI (**Ollama/Mistral**)  
- Builds a structured **knowledge base (CSV)**  
- Details **technical secrets** of each CAPTCHA variant  

---

## 💻 Interactive CLI
- Built with **Typer**  
- Provides a **user-friendly command-line interface**  
- Ensures **simple and efficient operation**  

---

## 🧰 Technologies Used

### 🐍 Language
- **Python 3.12+** with **asyncio** for high-performance asynchronous I/O  

### 🌐 Browser Automation
- **Playwright** for robust, headless browser control  
- Provides deep **mobile device emulation**  

### 🔗 HTTP Requests
- **curl_cffi** for making requests  
- Capable of **impersonating browser JA3/TLS fingerprints**  
- Bypasses many **network-level blocks**  

### ⚙️ CLI Framework
- **Typer** for building a clean, modern **command-line interface**  

### 🧩 HTML Parsing
- **BeautifulSoup** for **precise, deterministic, and fast parsing**  

### 🤖 Local AI (for analysis)
- **Ollama** to serve local LLMs:  
  - **Mistral** → text analysis  
  - **LLaVA** → vision tasks  

### ⚡ Configuration
- **pydantic-settings** for clean, **type-safe settings management** from `.env` files  

### 📜 Logging
- **loguru** for powerful, flexible, and **human-readable logging**  

## 🚧 Challenges, Solutions, and Perspectives

This project successfully navigated several classic **web scraping challenges**, evolving from a **simple script** into a **resilient toolkit**.

---

### ✅ What Has Been Done

#### 🛑 Challenge 1: Simple HTTP requests were instantly blocked or served CAPTCHAs  
**Solution:** A **hybrid approach** was developed.  
- A headless browser **warms up a session** to obtain valid cookies  
- Cookies are then reused by a **curl_cffi client with TLS impersonation**  
- This enables **fast and successful requests**  

---

#### 🛑 Challenge 2: CAPTCHA pages are complex and session-dependent, preventing a simple "scrape then solve" workflow  
**Solution:** A **robust fallback mechanism** was built.  
- When the fast method fails → launch a **full headed browser**  
- Perform the entire **search → solve → scrape** sequence in a **single persistent session**  
- Correctly handles **cookie banners** and **interactive forms** step by step  

---

#### 🛑 Challenge 3: The local AI (LLM) was initially slow and unreliable for parsing structured HTML search results  
**Solution:** The architecture was **pivoted**.  
- **AI removed** from time-sensitive scraping  
- Introduced a **fast, 100% reliable deterministic parser** with BeautifulSoup  
- Repurposed AI for **offline analysis** of complex, unstructured CAPTCHA pages  
- Leveraged AI’s **pattern-recognition strength** in the right context  

---

### 🔮 Perspectives for Future Development

- **🖼️ Full LLaVA Integration**  
  Complete the `ai_captcha_solver` by sending image grid screenshots to the **local LLaVA model** and mapping JSON responses into **browser clicks**.  

- **🗄️ Database Storage**  
  Upgrade the CSV-based knowledge base and logs to **SQLite** for better querying, indexing, and data management.  

- **🌍 Support for More Engines**  
  Abstract selectors & URLs in configs to add **DuckDuckGo**, **Bing**, and more with minimal effort.  

- **🖥️ GUI Interface**  
  Build a lightweight **GUI** (e.g., **Streamlit** or **PyQt**) to make the toolkit accessible to **non-technical users**.  
