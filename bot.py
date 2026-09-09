from pyrogram import Client

from info import API_ID, API_HASH, BOT_TOKEN


class AutoFilterBot(Client):

    def __init__(self):
        super().__init__(
            "AdvancedAutoFilterBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins={
                "root": "plugins"
            },
        )


app = Luttappibot()


if __name__ == "__main__":
    print("🚀 Advanced Auto Filter Bot Starting...")
    app.run()
