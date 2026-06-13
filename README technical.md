markdown
# Board Game Bot — Technical Documentation

## Concept Topic

### Purpose

This documentation is intended for developers who need to understand, modify, or extend 
the Board Game Bot. The bot is a Telegram-based recommendation system that helps users 
find board games by filtering a local database based on player count, play duration, 
and age restrictions.

### Target Audience

- Developers maintaining or extending the bot
- Students studying bot development or web scraping
- Contributors who want to add new features
- DevOps engineers deploying the bot to production

### Context of Use

Developers will read this documentation when they need to:

- Set up the bot locally or in Google Colab
- Understand how the scraping pipeline works
- Modify filtering logic or add new criteria
- Deploy the bot to a production environment
- Debug issues with the Telegram conversation flow

The bot consists of two main components:

1. **Telegram Bot** (`board_games_bot_py.py`) — handles user interaction
2. **Web Scraper** (`scraper_chatbot.py`) — collects game data from hobbygames.ru

---

## Functional Requirements
The product ensures the execution of the following key functions:
1. **Data Collection (Parsing):** Automatically browses the board game catalog,
   extracts game attributes (player count, age restrictions, duration, price,
   and description), and automatically determines the genre using descriptive keywords.
3. **Filtering:** Conducts a step-by-step user poll in Telegram to sequentially filter
   games based on the selected criteria.
5. **Pagination of Results:** Displays the matching games in the chat using interactive
   cards with navigation controls ("Next", "Previous") and a search reset option.

## Performance & Safety Requirements
* **Asynchronous Design:** User requests in the Telegram bot are processed using `asyncio`,
  which guarantees interface responsiveness even during concurrent use by multiple users.
* **Crawl Safety:** Network requests to the source website are optimized with random delays
  (ranging from 1.0 to 2.5 seconds) and `User-Agent` rotation to prevent server blocking
  (Rate Limiting).
* **Volume Control:** The maximum number of games fetched during a single parsing cycle is
  strictly regulated by a configuration file to save memory and network bandwidth.


## Project Structure
board-game-bot/\
│\
├── board_games_bot_py.py      # Main bot application (Telegram)\
├── scraper_chatbot.py          # Web scraper for game data\
├── config_chatbot.json         # Scraper configuration\
├── requirements.txt            # Python dependencies\
│\
└── board_games_data/           # Created by scraper\
....├── games_for_bot.json      # Game database (used by bot)\
....├── all_games.json          # Complete scraped data\
....├── game_1.json             # Individual game files\
....├── game_1_description.txt\
....└── ...

### Getting Started and Usage

### 1. Environment Setup
Install the necessary external libraries (according to the specified versions):
```bash
pip install -r requirements.txt
```
Note: If running inside Google Colab, the script automatically installs `nest_asyncio` 
to allow safe nested event loop execution.*

### 2. Data Gathering (Parser)
Before launching the bot, the database must be populated with up-to-date data. The parser 
is initiated through the crawler's internal `main()` function. Its behavior is 
modified in `config_chatbot.json`:
```json
{
  "seed_urls": ["https://hobbygames.ru"],
  "total_articles_to_find_and_parse": 100,
  "timeout": 30,
  "request_delay": {"min": 1.0, "max": 2.5},
  "max_retries": 3
}
```
Upon successful completion, the data will be compiled into `board_games_data/games_for_bot.json`.

### 3. Running the Telegram Bot
The integration with Telegram relies on the `python-telegram-bot` library (v20.7+). 
1. Assign your secret API token to the `TOKEN` variable inside the script.
2. Execute the script:
```bash
python board_games_bot.py
```

### 4. User Interaction Flow
The bot utilizes a Finite State Machine (`ConversationHandler`) to interact with users via 
an inline keyboard (`InlineKeyboardMarkup`):
1. **The `/start` command** — Starts a new search session and clears any previous user cache.
   The bot sends the first question.
3. **Player Count Selection** — The user picks the number of participants (from 1 up to 8+, or "Any").
4. **Duration Selection** — The bot inquires about available playtime ("Up to 30 min",
   "Up to 1 hour", "Up to 2 hours", or "Any").
6. **Age Filter** — The user specifies the target age group (6+, 12+, 18+).
7. **Results Display** — The bot processes the filters against the JSON data and presents game
   matching cards featuring descriptions, prices, genres, and navigation buttons. The session can be
   canceled at any stage using the `/cancel` command.
