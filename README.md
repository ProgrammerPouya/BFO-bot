# DylanGPT Dice Roller Bot

A Discord slash-command dice roller with **true randomness** (at least on the first roll).

## 🧱 Features

* Roll dice using the format:

  ```text
  AdB[kX][tY][+N|-N...]!Description
  ```

  Where:

  * `A` – number of dice
  * `B` – number of sides per die
  * `kX` – (optional) keep dice **≥ X**; lower results are crossed out and **don’t count** toward the sum
  * `tY` – (optional) target value; each kept die **≥ Y** counts as a success
  * `+N` / `-N` – (optional) integer modifiers applied to the final total
  * `!Description` – (optional) text description of the roll

* Uses **RANDOM.ORG** for the *first* die in each roll (true randomness), then falls back to Python’s `random` for the rest.
* Logs each roll invocation with timestamp in **PST** time.
* Works as a Discord slash command: `/roll`.

---

## 📦 Requirements

* Python 3.10+ (recommended)
* A Discord bot application (with a bot token)
* A RANDOM.ORG API key
* The packages listed in `requirements.txt`

---

## ⚙️ Setup

### 1. Clone the repo / download the files

Place the provided Python file `dylanGPT.py` and `requirements.txt` together in a folder.

---

### 2. Create and activate a virtual environment (recommended)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

---

### 3. Install dependencies

From the project directory:

```bash
pip install -r requirements.txt
```

---

### 4. Create your `.env` file

The bot expects you to create a `.env` file yourself in the **same directory** as the Python script.

Create a file named `.env` with the following contents:

```env
DISCORD_API_KEY=your_discord_bot_token_here
RANDORG_API_KEY=your_random_org_api_key_here
```

#### Getting these values

* **DISCORD_API_KEY**

  1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
  2. Create (or select) an application.
  3. Add a **Bot** to the application.
  4. Copy the **Bot Token** and paste it as `DISCORD_API_KEY`.

* **RANDORG_API_KEY**

  1. Go to [RANDOM.ORG](https://accounts.random.org/) and create a free account.
  2. Navigate to the API section.
  3. Generate an API key and paste it as `RANDORG_API_KEY`.

---

### 5. Invite your bot to a server

In the Discord Developer Portal:

1. Go to **OAuth2 → URL Generator**.
2. Check the scopes:
   * `bot`
   * `applications.commands`
3. Under **Bot Permissions**, give it at least:
   * `Send Messages`
4. Copy the generated URL and open it in your browser to invite the bot to your server.

---

### 6. Run the bot

From the project directory:

```bash
python dylanGPT.py
```

You should see the bot start up in the console. The first time it runs, it will sync the slash command tree.

## 🔢 Limits & Behavior

* `num_dice` is capped at **100**:

  ```python
  num_dice = 100 if num_dice > 100 else num_dice
  ```

* `sides` is capped at **2^31 - 1**:

  ```python
  sides = 2**31-1 if sides > 2**31-1 else sides
  ```

* The **first die** in each roll attempts to use true randomness via RANDOM.ORG:

  * If the API call fails, the bot logs this and falls back to `random.random()`.

* Timestamps in logs are localized to **America/Los_Angeles** using `pytz`.

---

## 🛠 Customization Ideas

* Change the timezone by editing:

  ```python
  PST = pytz.timezone('America/Los_Angeles')
  ```

* Adjust caps on dice count or sides.
* Tweak the response formatting for your own style or embed-based output.
* Expand the parser to support multiple dice expressions (e.g. `1d4+2d6-3`).
