# Max, what to watch?

This is a Telegram bot that can recommend movies and TV series. It can return a random movie and ask if you have seen it. Movies that you have seen are not shown again. You can a random movie for a specific tag or get a random set of tags to choose from.

The bot can be hosted as a serverless function.

Movies/TV series are stored in a Firebase storage. The number of requests for free is limited, so I try to cache the data in memory whenever possible. Even if the bot is hosted as a serverless function, it can exist in memory after it was called for a significat amount of time. There is no interface to edit data in the Firebase storage. I used to add new data with a script.

The bot also send usage data to Amplitude for basic analytics.
