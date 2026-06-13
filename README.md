Board Game Bot - User Guide
===========================

Concept Topic
-------------

### Purpose
Board Game Bot is designed to help users find suitable board games based
on their specific preferences. The bot eliminates the need to manually
browse through hundreds of games by providing personalized
recommendations through a simple question-answer interface.

### Target Audience
This bot is intended for:
- Board game enthusiasts looking for new games to play
- Families choosing games for game nights
- Groups of friends who need games matching their group size
- Event organizers selecting games for parties or gatherings
- Beginners who are not familiar with board game catalogues

### Context of Use
Users interact with the bot when they:
- Have a specific number of players (from 1 to 8+ people)
- Have limited time for playing (from 30 minutes to 2+ hours)
- Need age-appropriate games (for children, teenagers, or adults)
- Want to discover new board games without extensive research

The bot is accessible 24/7 via Telegram, making it convenient to use
on mobile devices or computers before a game session.

---

How to Find Board Games Using the Bot
=================================================

This text describes how to get personalized board game recommendations
by answering three questions about your gaming preferences. The bot
uses your answers to filter games from its database and displays
matching results.

Before you begin:
- Install Telegram on your device
- Have an internet connection
- Find the bot by username (@board_game_recommender_bot) or follow the
link https://web.telegram.org/k/#@board_game_recommender_bot

Procedure

1. Start the bot

   Open Telegram and type `/start` in the chat with Board Game Bot.
   
   Expected result: The bot displays a welcome message and asks
   about the number of players with inline buttons.
   
   "🎲 Добро пожаловать в бот подбора настольных игр!
   Я помогу найти игру по вашим предпочтениям."

3. Select the number of players

   Click one of the following buttons:

   - Numbers `1` through `7` for exact player count
   - `8+` for eight or more players
   - `🎲 Не важно` (Not important) to ignore this filter

   Expected result: The bot shows your selection and asks about
   available game duration.

5. Select available playing time

   Click one of the following buttons:

   - `⏱️ До 30 мин` (Up to 30 minutes)
   - `⏱️ До 1 часа` (Up to 1 hour)
   - `⏱️ До 2 часов` (Up to 2 hours)
   - `🎲 Не важно` (Not important) to ignore this filter

   Expected result: The bot shows your selections so far and asks
   about age restrictions.

6. Select age restriction

   Click one of the following buttons:

   - `🧒 6+ (6-11 лет)` for children's games
   - `👨 12+ (12-17 лет)` for teenage games
   - `👴 18+ (18+)` for adult games
   - `🎲 Не важно` (Not important) to ignore this filter

   Expected result: The bot filters games and displays the first
   matching game card.

7. Browse game recommendations

   Each game card shows:
   
      🎲 [1/5]
      *Game Title*
      👥 Игроки: 2-4
      ⏱ Время: 60 мин
      📅 Возраст: 12+
      🎭 Жанр: Strategy
      💰 Цена: 2500 руб
      📝 Описание:
      Game description text...

   Use the following buttons to navigate:

   - `◀️ Предыдущая` (Previous) - shows the previous game
   - `Следующая ▶️` (Next) - shows the next game
   - `🔄 Новый поиск` (New Search) - starts a new search from the beginning

9. If no games are found

   If the bot shows "Не нашлось игр под ваши критерии" (No games found):
   - Send `/start` to begin a new search
   - Select fewer filters or use "Не важно" (Not important) options
   - Choose broader criteria (e.g., more players, longer duration)

10. Cancel the search

   To stop the current search at any time, send `/cancel` command.
   
   Expected result: The bot ends the conversation. Send `/start`
   to begin again.

Example:
User: /start\
Bot: 🎲 Добро пожаловать в бот подбора настольных игр!\
Я помогу найти игру по вашим предпочтениям.\
👥 Сколько человек будет играть?\
User: [clicks "4"]\
Bot: 👥 Игроков: 4\
⏱️ Сколько времени у вас есть?\
User: [clicks "⏱️ До 1 часа"]\
Bot: 👥 Игроков: 4\
⏱️ Время: 60\
📅 Какое возрастное ограничение?\
User: [clicks "🧒 6+ (6-11 лет)"]\
Bot: [shows family-friendly games for 4 players under 60 minutes]

Commands Reference

- /start - Begin a new game search 
- /cancel - Cancel current search and end conversation

Troubleshooting

Problems and solutions:
- Bot does not respond - Send /start to restart the conversation
- No games found - Use "Не важно" (Not important) options for more results
- Buttons are not visible - Update Telegram app to the latest version
- Game description is cut off - Descriptions are limited to 500 characters in the current version

Additional Notes
- The bot interface is in Russian language
- No user data is permanently stored
