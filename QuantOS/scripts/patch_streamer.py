import os

path = 'core/data/streamer.py'
with open(path, 'r') as f:
    content = f.read()

# Update handle_trade
old_handle = """    async def handle_trade(self, data):
        symbol = data.symbol
        price = data.price
        await self.callback(symbol, 'trade', {'price': price})"""

new_handle = """    async def handle_trade(self, data):
        symbol = data.symbol
        price = data.price
        volume = getattr(data, 'size', 0)
        await self.callback(symbol, 'trade', {'price': price, 'volume': volume})"""

content = content.replace(old_handle, new_handle)

# Update IBKR polling loop
old_ibkr = """                            if price > 0:
                                await self.callback(symbol, 'trade', {'price': price})"""

new_ibkr = """                            if price > 0:
                                await self.callback(symbol, 'trade', {'price': price, 'volume': 0})"""

content = content.replace(old_ibkr, new_ibkr)

with open(path, 'w') as f:
    f.write(content)
print("Updated core/data/streamer.py")
