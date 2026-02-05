# TCP Connection Management

## Q1: Explain the TCP three-way handshake and four-way teardown process

### Three-Way Handshake

1. **Client → Server: SYN** - Client sends SYN packet with initial sequence number
2. **Server → Client: SYN-ACK** - Server acknowledges client's SYN + sends its own SYN
3. **Client → Server: ACK** - Client acknowledges server's SYN

### Four-Way Teardown

1. **Client → Server: FIN** - "I'm done sending data"
2. **Server → Client: ACK** - "I acknowledge your FIN"
3. **Server → Client: FIN** - "I'm also done sending data"
4. **Client → Server: ACK** - "I acknowledge your FIN"

---

# TCP Packet Loss and Retransmission

## What happens with packet loss? (Retransmission, exponential backoff)

### Packet Loss During the 3-Way Handshake

During the TCP 3-way handshake, any of the three packets (SYN, SYN-ACK, ACK) can be lost. TCP relies on timers and retransmission to recover.

### High-Level Behavior

1. Sender starts a timer whenever it sends a handshake segment (SYN or SYN-ACK)
2. If the expected ACK does not arrive before timeout, it assumes loss and retransmits the segment
3. Each retry waits longer than the previous one (exponential backoff) to avoid hammering a possibly congested network

### Concrete Cases

#### 1. Client's SYN is Lost

- Client sends SYN, starts a timer
- No SYN-ACK comes back (server never saw it), timer expires
- Client retransmits SYN, but now waits longer before the next retry (e.g., 1s, then 2s, then 4s, etc.)
- After some max number of retries/overall time (e.g., around 75 seconds on typical Linux configs), client gives up and reports "connection timed out"

#### 2. Server's SYN-ACK is Lost

- Server received the SYN, responded with SYN-ACK, starts its own timer while the connection is "half-open"
- Client never sees that SYN-ACK, so it doesn't send the final ACK
- When the server's timer expires, it retransmits the SYN-ACK, again using increasing delays between retries
- If the client eventually gets one of the SYN-ACKs, it sends the final ACK and the connection moves to ESTABLISHED on both sides
- If not, server eventually gives up and drops the half-open connection (helps mitigate SYN floods)

#### 3. Client's Final ACK is Lost

- Client got SYN-ACK, sent ACK
- Client now considers the connection ESTABLISHED
- Server doesn't see the ACK; its timer fires and it retransmits SYN-ACK once or a small number of times
- When client receives this "extra" SYN-ACK, it just sends ACK again; server finally transitions to ESTABLISHED
- Application on the client side usually doesn't notice this; it already thinks the connection is up

### Why Exponential Backoff?

TCP doesn't assume loss is always "random"; it often indicates congestion. If both endpoints hammer the network with frequent retries, they can make congestion worse.

**Exponential backoff:**
- Doubles the retransmission timeout after each failure (e.g., 1s → 2s → 4s → 8s...)
- Puts a cap on retries and eventual max delay, after which it closes the attempt

This is crucial in large systems: many clients failing fast and retrying aggressively can cause congestion collapse. Exponential backoff and capped retries keep things stable.

### Linux Configuration

On Linux these retry limits are kernel tunables exposed via sysctl under net.ipv4, specifically tcp_syn_retries and tcp_synack_retries. You can see and change them via /proc/sys/net/ipv4/* or sysctl, and make them persistent by putting them in /etc/sysctl.conf or a file under /etc/sysctl.d/.

## Can packet loss happen during the 4-way TCP teardown? How is it handled?

Yes, packet loss can absolutely happen during connection termination. TCP doesn't treat teardown as special; it uses the same retransmission and timeout logic it uses for data. Whenever a side sends a FIN, it starts a retransmission timer and stays in a closing state. If the corresponding ACK doesn't arrive in time, it retransmits the FIN, usually with exponential backoff and a cap on the number of retries.

### Concrete Example

For example, if my FIN is dropped, the peer won't respond. When my timer fires, I send the FIN again. If the peer's ACK to my FIN is dropped, I'll resend the FIN, and the peer will just send another ACK. If the peer's own FIN is dropped, it will retransmit that FIN until it sees my ACK. The final ACK isn't retransmitted directly, but if it's lost, the other side will retransmit its FIN, and I'll respond with another ACK.

### Key Insight

The net effect is: teardown is tolerant of loss, just like the 3-way handshake. The trade-off is that some connections may sit longer in states like FIN_WAIT or TIME_WAIT when there's packet loss, but the protocol still guarantees an orderly, reliable close.