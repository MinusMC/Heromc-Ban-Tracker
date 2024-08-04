# Heromc Ban Tracker

**MADE BY:** **ndiep.2006_ and idle.zzz**

## How to Use

Welcome to the Heromc Ban Tracker! This tool can automatically fetch IDs.

### Setup

1. **Bot Token or Webhook**:
   - If using a bot, provide the bot token.
   - If using a webhook, provide the webhook URL.

### Features

- **Automatic ID Fetching**: Simplifies the process of tracking bans.
- **User-Friendly Interface**: Easy to set up and use.

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/MinusMC/Heromc-Ban-Tracker
    ```

2. Navigate to the project directory:

    ```bash
    cd Heromc-Ban-Tracker
    ```

3. Install dependencies using:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the project:

    ```bash
    python main.py
    ```

### Configuration

- Open the configuration file and add your bot token or webhook URL:

    ```json
    {
      "BOT_TOKEN": "YOUR_BOT_TOKEN",
      "CHANNEL_ID": 1268756066544517191, // Replace with your channel ID
      "GUILD_ID": 1240969902265864202,   // Replace with your guild ID
      "REFRESH_TIME": 1
    }
    ```

### Example Usage

Here's an example of how to use the Heromc Ban Tracker:

1. **Create a `config.json` file**:
    - Add your bot token, channel ID, guild ID, and refresh time as shown in the configuration section.

2. **Run the tracker**:
    - Execute the following command to start the tracker:

    ```bash
    python main.py
    ```

## Preview

![Preview Image](https://cdn.discordapp.com/attachments/1262641976633851996/1269453856287227924/image.png?ex=66b01e88&is=66aecd08&hm=f7da52ca3c5ecd0705ba25d3808dd02a18b308dad263024b9b0d8b7e8fa37388&)
