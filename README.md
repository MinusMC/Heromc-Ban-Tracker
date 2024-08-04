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

1. Clone the repository.
2. Navigate to the project directory.
3. Install dependencies using:

    ```bash
    npm install
    ```

4. Run the project:

    ```bash
    npm start
    ```

### Configuration

- Open the configuration file and add your bot token or webhook URL:

    ```json
    {
    "BOT_TOKEN": "YOUR_BOT_TOKEN",
    "CHANNEL_ID": 1268756066544517191, //* Replace with your chanel id
    "GUILD_ID": 1240969902265864202,   //* Replace with yout guild id
    "REFRESH_TIME": 1
    }
    ```

### Example Usage

Here's an example of how to use the Heromc Ban Tracker:

```javascript
const banTracker = require('heromc-ban-tracker');

banTracker.init({
  botToken: 'YOUR_BOT_TOKEN',
});

banTracker.track();
