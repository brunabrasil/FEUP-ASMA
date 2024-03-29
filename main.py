import spade
from environment import Environment

async def main():
    environment = Environment("environment@localhost", "password")
    await environment.start()

if __name__ == "__main__":
    spade.run(main())