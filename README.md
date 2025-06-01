# Tour Telegram Bot (TTB)

**Tour Telegram Bot** is a project to create and host text, photo, and audio tours via a Telegram bot.

---

## 📌 Current Status

This project is currently in **early alpha** version and is under **heavy development**.  
Feel free to **clone**, **modify** it for your needs, or create **pull requests**.

---

## 📄 Documentation

### Preparing environment 
First we need to set up python development environment.

If you are using IDE with auto project setup (e.g. PyCharm) use it's built in setup process.

Otherwise, you can use following commands to set up development stand:

1. Clone repository:
```shell
  git clone https://github.com/CAPGAGA/tour-telegram-bot.git && cd tour-telegram-bot
```
2. Setup python virtual environment:
```shell
  python -m venv venv
```
3. Install needed dependencies 
```shell
  pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
```
4. Setup `.env` file with `.env.example`
5. Export env into your virtual environment:
```shell
  export $(xargs < .env)
```

### Adding new language

### Translating to new language
To translate to new language first:

Run to extract all needed for translation strings from py and html (with jinja2) templates :

```shell
pybabel extract -F babel.cfg -o messages.pot .
```

Then initialize your translation file with:
```shell
pybabel update -i messages.pot -d lang
```

Translate in lang/<lang>/LC_MESSAGES/messages.po and compile with

```shell
pybabel compile -d lang
```

---

## 📬 Contacts

- **GitHub**: [CAPGAGA](https://github.com/CAPGAGA)
- **Telegram**: [@captain_gaga](https://t.me/captain_gaga)

---

## ✨ Features

1. **Built-in API** and **admin panel** to manage tours and users.
2. Integration with **Telegram API**.
3. Integration with payment systems (built-in Telegram, **Prodamus**).
4. Built-in **SQLite database** with all necessary tables.