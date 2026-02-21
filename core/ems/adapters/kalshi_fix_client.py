import asyncio
import simplefix
import os
import time
from datetime import datetime, timezone

class KalshiFIXClient:
    def __init__(self, host: str, port: int, sender_comp_id: str, target_comp_id: str):
        self.host = host
        self.port = port
        self.sender_comp_id = sender_comp_id
        self.target_comp_id = target_comp_id
        self.password = os.getenv("KALSHI_PASSWORD", "")
        self.msg_seq_num = 1
        self.reader = None
        self.writer = None
        self.is_connected = False

    def _create_message(self, msg_type: str) -> simplefix.FixMessage:
        """Constructs base header for FIX 4.4."""
        msg = simplefix.FixMessage()
        msg.append_pair(8, "FIX.4.4", header=True)
        msg.append_pair(35, msg_type, header=True)
        msg.append_pair(34, self.msg_seq_num, header=True)
        msg.append_pair(49, self.sender_comp_id, header=True)
        msg.append_pair(56, self.target_comp_id, header=True)
        
        utc_now = datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]
        msg.append_pair(52, utc_now, header=True)
        
        self.msg_seq_num += 1
        return msg

    async def connect_and_logon(self):
        """Initial Logon (35=A) sequence."""
        print(f"📡 FIX: Connecting to Kalshi at {self.host}:{self.port} (SSL)...")
        try:
            import ssl
            ssl_context = ssl.create_default_context()
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port, ssl=ssl_context
            )
            
            # Logon message
            msg = self._create_message("A")
            msg.append_pair(98, "0")   # EncryptMethod
            msg.append_pair(108, "30") # Heartbeat Interval
            msg.append_pair(554, self.password) # Password
            
            await self._send(msg)
            self.is_connected = True
            
            # Start background session tasks
            asyncio.create_task(self._heartbeat_loop())
            asyncio.create_task(self._receiver_loop())
            
            print("✅ FIX: Logon dispatched. Session active.")
        except Exception as e:
            print(f"❌ FIX: Boot failure: {e}")
            self.is_connected = False

    async def _send(self, msg: simplefix.FixMessage):
        if not self.writer: return
        encoded = msg.encode()
        self.writer.write(encoded)
        await self.writer.drain()
        # Log sanitized bytes
        readable = encoded.replace(b'\x01', b'|')
        print(f"--> FIX OUT: {readable}")

    async def _heartbeat_loop(self):
        """35=0 keeps the TCP pipe open."""
        while self.is_connected:
            await asyncio.sleep(30)
            hb = self._create_message("0")
            await self._send(hb)

    async def _receiver_loop(self):
        parser = simplefix.FixParser()
        while self.is_connected:
            try:
                data = await self.reader.read(4096)
                if not data:
                    print("❌ FIX: Socket closed by peer.")
                    self.is_connected = False
                    break
                
                parser.append_buffer(data)
                msg = parser.get_message()
                while msg:
                    mtype = msg.get(35).decode()
                    if mtype == "8": # Execution Report
                        print(f"🚨 FIX: TRADE EXECUTED: {msg}")
                    msg = parser.get_message()
            except Exception as e:
                print(f"❌ FIX: Receiver error: {e}")
                break

    async def send_order(self, ticker: str, action: str, qty: int, price: float):
        """Dispatches a NewOrderSingle (35=D)."""
        msg = self._create_message("D")
        
        cl_ord_id = f"CL-{int(time.time())}"
        msg.append_pair(11, cl_ord_id) # ClOrdID
        msg.append_pair(55, ticker)    # Symbol
        msg.append_pair(54, "1" if action.lower() == "buy" else "2") # Side
        msg.append_pair(38, qty)       # OrderQty
        msg.append_pair(44, price)     # Price
        msg.append_pair(40, "2")       # OrdType=Limit
        msg.append_pair(59, "0")       # TimeInForce=Day
        msg.append_pair(60, datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]) # TransactTime
        
        await self._send(msg)
        print(f"⚡ FIX: NewOrderSingle dispatched for {ticker} ({action})")
