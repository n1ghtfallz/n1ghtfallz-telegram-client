# ntc - n1ghtfallz Telegram Client

A powerful, terminal-based Telegram client built with Python, Telethon, and Rich.

## Features

*   **Terminal Interface**: Clean, dark-themed CLI interface.
*   **Rich UI**: Tables, formatted text, and animations using the Rich library.
*   **Multi-language Support**: English, Russian, Ukrainian, Kazakh.
*   **Message Management**: Send, reply, edit, delete, forward, and pin messages.
*   **Media Support**: Download and send images/files.
*   **Interactive Shell**: Command loop for continuous usage.
*   **Themes**: Switch between Dark, Light, Purple, and Matrix themes.
*   **Slot Machine**: A fun mini-game included.

## Installation

1.  **Clone the repository** (or download the files):
    ```bash
    git clone https://github.com/n1ghtfallz/n1ghtfallz-telegram-client.git
    cd ntc
    ```

2.  **Install dependencies**:
    Make sure you have Python 3.10+ installed.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Get API Credentials**:
    *   Go to [https://my.telegram.org](https://my.telegram.org)
    *   Log in and go to "API development tools".
    *   Create a new application to get your `API_ID` and `API_HASH`.

4.  **Setup Environment**:
    *   Run the script for the first time, and it will prompt you for credentials.
    *   OR create a `.env` file manually:
        ```env
        API_ID=12345678
        API_HASH=your_api_hash_here
        ```

## Usage

Run the client:
```bash
python ntc.py
```

### Commands

Once inside the interactive shell (`>`), you can use the following commands:

**Chats & Navigation**
*   `list` or `l`: List recent chats.
*   `select <n>` or `s <n>`: Select a chat by its number from the list.
*   `msg [n]` or `m [n]`: Show last `n` messages in the current chat.
*   `search <text>` or `sr <text>`: Search messages in the current chat.

**Messaging**
*   `send <text>` or `sd <text>`: Send a message to the current chat.
*   `reply <n> <text>` or `r <n> <text>`: Reply to message number `n`.
*   `edit <n> <text>`: Edit your message number `n`.
*   `del <n>` or `d <n>`: Delete message number `n`.
*   `react <n> <emoji>`: React to a message.
*   `forward <n>` or `f <n>`: Forward message `n` to Saved Messages.

**Media**
*   `img <n>` or `i <n>`: Download media from message `n`.
*   `send-img <path>` or `si <path>`: Send an image/file from the given path.

**Profile & Settings**
*   `mp`: Show your profile.
*   `name <First> [Last]`: Change your display name.
*   `bio <text>`: Change your bio.
*   `cu <username>`: Change your username.
*   `theme <name>`: Change theme (dark, light, purple, matrix).
*   `language <code >`: Change language (en, ru, uk, kk).

**Other**
*   `slots`: Play the slot machine.
*   `saved`: Go directly to Saved Messages.
*   `logout`: Log out of the session.
*   `exit`: Exit the application.

## Requirements

*   Python 3.10+
*   `telethon`
*   `rich`
*   `python-dotenv`

## License

Made for fun by n1ghtfallz.
