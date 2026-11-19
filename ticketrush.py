"""
CADA NEU - NoSQL Databases
CHAPTER 2: KEY-VALUE STORE (REDIS) - CORE LAB
TicketRush: High-Concurrency Concert Ticket Booking Backend
"""

import time
import uuid
from concurrent.futures import ThreadPoolExecutor
import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def race(fn, n=50):
    """Thực thi fn(i) đồng thời từ n threads và trả về danh sách kết quả."""
    with ThreadPoolExecutor(max_workers=n) as pool:
        return list(pool.map(fn, range(n)))

def hold_naive(event: str, seat: str, user: str, ttl: int = 300) -> bool:
    """Phiên bản lỗi: GET rồi mới SET (Check-Then-Act Race Condition)."""
    key = f"hold:{event}:{seat}"
    if r.get(key) is None:
        time.sleep(0.001)  
        r.set(key, user, ex=ttl)
        return True
    return False

def hold_nx(event: str, seat: str, user: str, ttl: int = 300) -> bool:
    """Phiên bản chuẩn nguyên tử: Dùng SET với tham số NX (Not Exists) và EX (TTL)."""
    key = f"hold:{event}:{seat}"

    return bool(r.set(key, user, nx=True, ex=ttl))


HOLD_SCRIPT = r.register_script("""
if redis.call('SISMEMBER', KEYS[2], ARGV[2]) == 1 then
    return 0 -- Ghế đã được bán hoàn tất, không thể giữ
end
if redis.call('SET', KEYS[1], ARGV[1], 'NX', 'EX', ARGV[3]) then
    return 1 -- Giữ ghế thành công
end
return 0 -- Đang có người khác giữ
""")


CONFIRM_SCRIPT = r.register_script("""
if redis.call('GET', KEYS[1]) == ARGV[1] then
    redis.call('SADD', KEYS[2], ARGV[2]) -- Thêm vào danh sách đã bán
    redis.call('DEL', KEYS[1])           -- Xoá lock giữ tạm
    return 1 -- Mua vé thành công
end
return 0 -- Người thanh toán không phải người đang giữ ghế (hoặc hết hạn TTL)
""")


RELEASE_SCRIPT = r.register_script("""
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1]) -- Chỉ chủ sở hữu mới được tự huỷ giữ ghế
end
return 0
""")

def hold(event: str, seat: str, user: str, ttl: int = 300) -> bool:
    return bool(HOLD_SCRIPT(keys=[f"hold:{event}:{seat}", f"sold:{event}"], args=[user, seat, ttl]))

def confirm(event: str, seat: str, user: str) -> bool:
    return bool(CONFIRM_SCRIPT(keys=[f"hold:{event}:{seat}", f"sold:{event}"], args=[user, seat]))

def release(event: str, seat: str, user: str) -> bool:
    return bool(RELEASE_SCRIPT(keys=[f"hold:{event}:{seat}"], args=[user]))

def seat_map(event: str, seats: list) -> dict:
    """Trả về trạng thái hiện tại của từng ghế: 'sold', 'held', hoặc 'free'."""
    sold = r.smembers(f"sold:{event}")
    return {
        s: "sold" if s in sold else "held" if r.exists(f"hold:{event}:{s}") else "free"
        for s in seats
    }


def buy_general(event: str, user: str) -> bool:
    """
    Bán vé dạng đếm kho (counter).
    Dùng DECR nguyên tử để trừ kho. Nếu âm thì INCR lại để hoàn trả.
    """
    left = r.decr(f"stock:{event}")
    if left < 0:
        r.incr(f"stock:{event}")  # Hoàn tác: kho đã hết vé
        return False
    r.sadd(f"buyers:{event}", user)
    return True


def allow_fixed(user: str, limit: int = 5, window: int = 10) -> bool:
    """Fixed Window Rate Limiter: INCR + EXPIRE qua Pipeline."""
    bucket = int(time.time() // window)
    key = f"rl:fixed:{user}:{bucket}"
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, window, nx=True)
    count, _ = pipe.execute()
    return count <= limit


SLIDING_SCRIPT = r.register_script("""
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]

-- Xoá các mốc thời gian ngoài cửa sổ trượt (now - window)
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, now - window)

-- Đếm số request trong cửa sổ hiện tại
if redis.call('ZCARD', KEYS[1]) < limit then
    redis.call('ZADD', KEYS[1], now, member)
    redis.call('PEXPIRE', KEYS[1], window)
    return 1 -- Được phép
end
return 0 -- Bị chặn do vượt quá rate limit
""")

def allow_sliding(user: str, limit: int = 5, window_ms: int = 10_000) -> bool:
    now_ms = int(time.time() * 1000)
    req_id = uuid.uuid4().hex
    return bool(SLIDING_SCRIPT(keys=[f"rl:sliding:{user}"], args=[now_ms, window_ms, limit, req_id]))


def join_queue(event: str, user: str) -> int:
    """
    Người dùng tham gia hàng đợi ảo.
    Score là timestamp (ai vào trước có score nhỏ hơn).
    Trả về vị trí xếp hàng (1-based rank).
    """
    key = f"queue:{event}"
  
    r.zadd(key, {user: time.time()}, nx=True)
    rank = r.zrank(key, user)
    return rank + 1 if rank is not None else -1

def admit(event: str, n: int) -> list:
    """Lấy ra n người đứng đầu hàng đợi để cho phép vào mua vé."""
    key = f"queue:{event}"

    popped = r.zpopmin(key, n)
    return [user for user, score in popped]


def run_stress_test():
    print("\n" + "="*70)
    print("BƯỚC 6: STRESS TEST HỆ THỐNG TICKETRUSH")
    print("Mô tả: 100 users đồng thời tranh mua 20 ghế (A01 -> A20)")
    print("="*70)
    
    event = "concert_live"
    seats = [f"A{i:02d}" for i in range(1, 21)] 
    
    r.flushdb()
    
 
    def user_flow(user_idx):
        user = f"user_{user_idx:03d}"
        import random

        target_seat = random.choice(seats)
        if hold(event, target_seat, user, ttl=10):

            time.sleep(random.uniform(0.001, 0.005))
 
            return confirm(event, target_seat, user)
        return False

    results = race(user_flow, n=100)
    
    sold_count = sum(1 for res in results if res is True)
    sold_set = r.smembers(f"sold:{event}")
    
    print(f" - Số giao dịch thanh toán thành công (confirmed) : {sold_count}")
    print(f" - Số lượng ghế trong tập 'sold:{event}'             : {len(sold_set)}")
    print(f" - Danh sách ghế đã bán: {sorted(list(sold_set))}")
    

    assert sold_count <= len(seats), f"LỖI: Bán quá số ghế ({sold_count} > {len(seats)})!"
    assert sold_count == len(sold_set), f"LỖI: Dữ liệu không nhất quán ({sold_count} != {len(sold_set)})!"
    print("\n=> KẾT QUẢ: PASS! Không xảy ra Over-selling hay Duplicate Booking!")
if __name__ == "__main__":
    try:
        r.ping()
        print("Đã kết nối Redis thành công!\n")
        
  
        print("--- THỬ NGHIỆM BƯỚC 1: GIỮ GHẾ ĐỒNG THỜI ---")
        r.flushdb()
        naive_wins = race(lambda i: hold_naive("c1", "A1", f"user{i}"), n=50)
        print(f"[hold_naive] Số người tưởng mình giữ được ghế A1: {sum(naive_wins)} (LỖI RACE CONDITION!)")
        
        r.flushdb()
        nx_wins = race(lambda i: hold_nx("c1", "A1", f"user{i}"), n=50)
        print(f"[hold_nx]    Số người giữ được ghế A1            : {sum(nx_wins)} (CHÍNH XÁC: ĐÚNG 1 NGƯỜI!)\n")
     
        print("--- THỬ NGHIỆM BƯỚC 2: ATOMIC HOLD / CONFIRM / RELEASE ---")
        r.flushdb()
        print("Linh giữ A1:", hold("c1", "A1", "linh"))
        print("Nam cố giữ A1:", hold("c1", "A1", "nam"))
        print("Nam cố xác nhận A1:", confirm("c1", "A1", "nam"))
        print("Linh xác nhận thanh toán A1:", confirm("c1", "A1", "linh"))
        print("Nam cố giữ lại A1 sau khi đã bán:", hold("c1", "A1", "nam"))
        print("Trạng thái ghế:", seat_map("c1", ["A1", "A2"]))
        
       
        print("\n--- THỬ NGHIỆM BƯỚC 3: FLASH SALE VÉ KHÔNG ĐÁNH SỐ GHẾ ---")
        r.flushdb()
        r.set("stock:g1", 50)
        ga_results = race(lambda i: buy_general("g1", f"user{i}"), n=200)
        print(f"Bán ra: {sum(ga_results)} vé | Còn lại trong kho: {r.get('stock:g1')} | Khách mua: {r.scard('buyers:g1')}")
        
      
        print("\n--- THỬ NGHIỆM BƯỚC 4: RATE LIMITING ---")
        fixed_checks = [allow_fixed("linh", limit=3, window=10) for _ in range(5)]
        print(f"Fixed Window (limit 3): {fixed_checks}")
        sliding_checks = [allow_sliding("linh", limit=3, window_ms=5000) for _ in range(5)]
        print(f"Sliding Window (limit 3): {sliding_checks}")
        
        
        print("\n--- THỬ NGHIỆM BƯỚC 5: PHÒNG CHỜ ẢO ---")
        r.flushdb()
        print("User A vào hàng, thứ tự:", join_queue("event1", "User_A"))
        print("User B vào hàng, thứ tự:", join_queue("event1", "User_B"))
        print("User C vào hàng, thứ tự:", join_queue("event1", "User_C"))
        admitted = admit("event1", 2)
        print("Cho phép 2 người đầu tiên vào:", admitted)
        
        
        run_stress_test()
        
    except Exception as e:
        print(f"[LỖI KẾT NỐI]: {e}. Vui lòng khởi động Redis qua Docker Compose trước khi chạy.")
