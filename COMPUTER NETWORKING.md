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


## What is TIME_WAIT state and why does it exist?

### What TIME_WAIT Is

After the final ACK is sent in the four-way teardown, that side enters **TIME_WAIT** for **2 × MSL** (Maximum Segment Lifetime).

- MSL is the theoretical maximum time any packet can live in the network
- Common implementations: 30-60 seconds
- OS keeps the 4-tuple (source IP, source port, dest IP, dest port) and sequence state
- No new connection can reuse the same 4-tuple until TIME_WAIT expires

### Why TIME_WAIT Exists

**1. Absorb delayed/duplicate segments from old connection**
- Delayed packets from the old connection might arrive after close
- Without TIME_WAIT, if a new connection reused the same 4-tuple, stray packets could be misinterpreted
- TIME_WAIT keeps old connection context alive to recognize and discard duplicates

**2. Reliably deliver the final ACK**
- If the final ACK is lost, the peer will retransmit its FIN
- While in TIME_WAIT, the endpoint can still receive that FIN and send another ACK
- Without TIME_WAIT, couldn't respond properly and peer might think connection closed abnormally

### Production Implications

- Busy servers accumulate large numbers of TIME_WAIT sockets
- Can exhaust ephemeral ports or consume memory/connection tracking slots
- **Common mitigations:**
  - Use persistent connections (HTTP keep-alive, connection pooling)
  - Move connection initiation to client side (clients pay TIME_WAIT cost)
  - Careful TCP parameter tuning (understanding the risks)

**Core insight:** TIME_WAIT is a safety buffer preventing old packets from interfering with new connections and ensuring clean, acknowledged close.

## What is connection pooling and why is it important?

### What Connection Pooling Is

A pool is a managed set of open, ready-to-use connections (e.g., to a DB or backend service).

When a request comes in, the app borrows a connection from the pool, uses it, then returns it instead of closing it.

Under the hood, each pooled connection already paid all the setup costs: TCP 3-way handshake, TLS handshake, authentication, and DB session setup.

**Example: web app using a DB driver + pool:**
- App starts; pool opens N TCP connections to the DB and authenticates
- Each HTTP request that needs the DB checks out a connection, runs queries, returns it
- Idle connections stay open (up to configured limits) for reuse

### Why We Need Pooling (Production View)

**Without pooling, every operation does:**
1. DNS (maybe)
2. TCP 3-way handshake
3. TLS handshake
4. Auth/session setup (DB or app-level)
5. Do work
6. Four-way FIN teardown and TIME_WAIT

**Costs in production:**
- Extra latency per request (several RTTs for TCP+TLS+auth)
- High CPU and memory overhead on backends from constantly creating/destroying sessions
- Kernel overhead and TIME_WAIT explosion from lots of short-lived TCP connections
- Risk of exhausting file descriptors, ephemeral ports, or DB connection limits

**Pooling amortizes all that over many requests:**
- **Lower latency:** skip repeated handshake/auth; reuse "warm" connections
- **Higher throughput:** backend spends time doing work, not handshakes
- **Resource control:** pool size caps concurrent connections to DB or microservice, providing backpressure instead of connection storms
- **Fewer TIME_WAIT sockets:** far fewer connect/close cycles

### How Pooling Is Typically Implemented

**Common patterns across HTTP and DB:**
- **Max pool size:** upper bound on concurrent connections to a backend
- **Min / idle connections:** how many to keep pre-warmed
- **Max lifetime / idle timeout:** how long a connection can live or sit idle before being closed and refreshed
- **Validation / health checks:** small "ping" or simple query before handing a connection out, to avoid giving callers a broken connection

**Examples:**
- HTTP client libraries (Java, Go, .NET, etc.) keep a pool of keep-alive connections per host
- DB pools (HikariCP, pgBouncer, RDS Proxy, etc.) sit between app and DB, managing a fixed number of TCP/DB sessions

### How This Ties Back to TCP Handshake/Teardown/TIME_WAIT

**Pooling reduces:**
- Number of TCP handshakes – you establish far fewer connections
- Number of TCP 4-way teardowns – you close far fewer sockets
- Amount of TIME_WAIT – because far fewer connections reach teardown per second

**Result:**
- Less packet churn and fewer retransmission opportunities
- Lower risk of hitting ephemeral port limits or kernel conn-tracking limits
- Smoother behavior during bursts: instead of a storm of TCP connects, requests queue on the pool

### How to Explain It in an Interview

**If they ask: "What is connection pooling and why is it important in production systems?"**

You can answer:

*Connection pooling is a technique where the application keeps a pool of open TCP connections to a backend – usually a database or another service – and reuses them across many requests instead of opening and closing a new connection each time. Each pooled connection has already done the TCP 3-way handshake, TLS handshake, and authentication, so a request can borrow it, do work, and return it without paying those costs again.*

**Then hit benefits and tie back to TCP:**

*In production this matters for three reasons. First, it reduces latency because you avoid repeated TCP+TLS handshakes and DB logins on every call. Second, it dramatically lowers load on the backend and the OS: you're not constantly creating and tearing down connections, so you avoid large numbers of sockets in TIME_WAIT, file-descriptor pressure, and connection storms. Third, it gives you backpressure and control – the pool size caps how many concurrent connections you open to a backend, and extra requests either wait for a free connection or fail fast instead of overwhelming the service.*

**And show that you understand configuration trade-offs:**

*Typically you tune parameters like max pool size, min idle, max lifetime, and idle timeout. Too small a pool and you serialize throughput; too large and you can overload the database or run into resource limits. So in practice, I'll size pools based on expected QPS, backend connection limits, and latency SLOs, and then monitor metrics like pool utilization, wait time for a connection, and backend CPU.*

**If they explicitly ask how this relates to TIME_WAIT / handshake:**

*Because we reuse connections, we do far fewer TCP three-way handshakes and four-way teardowns, which means fewer sockets entering TIME_WAIT. That's why on busy systems the right answer is usually "better pooling and keep-alive" rather than hacking around TCP TIME_WAIT semantics.*

---

# TCP vs UDP

## Core Difference

**TCP:** Connection-oriented, reliable, ordered, with congestion control and flow control; higher overhead, higher latency.

**UDP:** Connectionless, unreliable (no delivery/order guarantee), no built-in congestion control; low overhead, low latency.

## When to Use Each

**Use TCP when correctness matters more than latency:**
- Web browsing (HTTP/HTTPS)
- File transfer
- Email
- APIs
- Database protocols

**Use UDP when low latency matters more than perfect reliability:**
- VoIP
- Live video/audio streaming
- Online gaming
- DNS
- Custom real-time protocols (often with app-level reliability if needed)

## Production Examples

- **DNS:** Uses UDP for quick lookups, falls back to TCP for large responses
- **Video Streaming:** UDP for real-time data, TCP for control messages
- **HTTP/3:** Uses UDP with QUIC protocol for better performance

Key Insight: Many production systems use both protocols strategically based on the specific
requirements of each component.
---

# IPv4 vs IPv6

## Core Difference: IPv4 vs IPv6

**IPv4** uses 32-bit addresses, giving about 4.3 billion addresses total (2³²), which we've effectively exhausted.

**IPv6** uses 128-bit addresses, giving about 340 undecillion addresses (2¹²⁸), effectively "infinite" at human scale.

**Notation and basics:**
- **IPv4:** dotted decimal, e.g. 192.168.1.10
- **IPv6:** hexadecimal with colons, e.g. 2001:0db8:85a3:0000:0000:8a2e:0370:7334 (often shortened with ::)

## Why We Needed IPv6

### IPv4 Limitations
- Limited address space → address exhaustion, driving workarounds like large-scale NAT
- Heavy dependence on NAT breaks true end-to-end connectivity and complicates troubleshooting
- Security and QoS are bolt-ons, not baked into the protocol itself

### IPv6 Advantages
- **Vast address space:** direct addressing for essentially all devices, no need for widespread NAT
- **Built-in IPsec support,** and better support for extensions like privacy addresses
- **More efficient, fixed-size header** and better routing aggregation → simpler, more scalable routing
- **Better support for auto-configuration and mobility** (SLAAC, Neighbor Discovery, etc.)

## Production / SRE Angle

In real systems, you usually run both IPv4 and IPv6:

- **Dual stack:** interfaces and services listen on both IPv4 and IPv6; apps and clients pick what to use (Happy Eyeballs, etc.)
- **Transition/translation:** DNS64 + NAT64 to let IPv6-only clients reach IPv4 services, or vice versa
- **Infra support:** load balancers, proxies, firewalls, and observability tools need full IPv6 support (policies, logs, metrics)
- **Monitoring:** track reachability and performance on both stacks; IPv6 paths can behave differently from IPv4

## How to Say It in an Interview

You could answer like this:

*IPv4 uses 32-bit addresses, so we only get about 4.3 billion addresses, which has led to address exhaustion and a heavy reliance on NAT. IPv6 uses 128-bit addresses, which gives us on the order of 340 undecillion addresses, so we can give almost every device a globally unique address.*

**Then explain "why IPv6":**

*We need IPv6 mainly to solve IPv4 address exhaustion and to restore simpler, end-to-end connectivity without layers of NAT. It also adds improvements like built-in IPsec support, a simpler fixed-length header for more efficient routing, and better auto-configuration and mobility features.*

**And add a short production-engineering angle:**

*In production you almost always run dual stack and deal with transition mechanisms like NAT64 and DNS64 so IPv6-only workloads can still talk to IPv4 services. As an SRE I care that my load balancers, firewalls, and monitoring all handle IPv6 correctly, and I watch connectivity and performance on both stacks because they can behave differently.*

---

# NAT and IPv4 Exhaustion

## How NAT Mitigates IPv4 Exhaustion

NAT is basically a workaround that lets many private IPv4 hosts share a few public IPv4 addresses, slowing down exhaustion.

### Private vs Public Space

**RFC1918 defines private IPv4 ranges** (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) that are not routed on the public Internet.

Inside a home/enterprise/ISP, you can reuse these ranges for thousands or millions of devices without consuming public addresses.

### What NAT Does

A NAT device (router, firewall, or CGNAT at ISP) sits at the edge.

**On outbound traffic, it rewrites:**
- Source private IP + source port → its own public IP + some chosen port

**On inbound responses,** it looks up that mapping and rewrites the packet back to the internal private IP/port.

**Effect:**
- To the Internet, hundreds or thousands of internal devices all look like one public IPv4 (or a small pool)
- This dramatically reduces how many public IPv4 addresses an enterprise or ISP needs

### How This Mitigates IPv4 Exhaustion

**Without NAT,** every device that wants to talk to the Internet needs a globally unique public IPv4 address.

**With NAT:**
- **Enterprises:** can put all internal hosts on RFC1918 space and use a single public IPv4 on the edge
- **ISPs (Carrier-Grade NAT):** can assign private addresses to customers and share public IPv4s among many subscribers

This has been one of the main operational tools that let IPv4 survive long after the global pools "ran out."

**Trade-offs:**
- Breaks true end-to-end addressing, complicates some protocols and P2P, adds state and complexity on middleboxes
- It's a band-aid, not a long-term fix; IPv6 is the standards-based solution

## How to Say It in an Interview

**If they ask: "Explain how NAT is used for IPv4 exhaustion":**

*IPv4 only has about 4.3 billion addresses, which isn't enough for every device to have a unique public IP, so we'd have hit the wall much earlier without NAT. NAT lets many private hosts share a much smaller pool of public addresses.*

**Then add one clear sentence on mechanics:**

*Inside a network we use RFC1918 private ranges, and the edge router translates internal private IPs and ports to one or a few public IPv4 addresses on outbound traffic, and reverses the mapping on replies.*

**Then tie explicitly to exhaustion:**

*That way, an enterprise or ISP can support thousands or millions of devices while consuming only a small number of public IPv4 addresses. It's been a key mitigation for IPv4 exhaustion, although it comes at the cost of losing true end-to-end connectivity and adding complexity, which is part of why we ultimately need IPv6.*

---

# DNS Lookup Process

## Q4: Walk me through what happens during a DNS lookup for www.facebook.com

### Step-by-Step Process

1. **Browser Cache Check** - Local DNS cache lookup
2. **OS Resolver Cache** - System-level cache check
3. **Local DNS Server** - ISP or configured DNS server query
4. **Root Server Query** - Returns .com nameserver information
5. **TLD Server Query** - .com server returns facebook.com nameserver
6. **Authoritative Server** - facebook.com nameserver returns actual IP address
7. **Response Caching** - Result cached at each level with TTL values

### Types of Queries

- **Recursive:** Client asks resolver to get the complete answer
- **Iterative:** Server returns next server to query instead of complete answer

### Key Production Considerations

- DNS failures can cause complete service outages
- TTL values affect both performance and flexibility
- Multiple A records enable load balancing
- DNSSEC for security in critical environments

## High-Level Story

When I type www.facebook.com in the browser, the system walks through several layers of cache and DNS servers to translate that name into an IP address, then caches the result using TTLs.

## Detailed Step-by-Step Lookup

1. **Browser cache** – Browser first checks its own DNS cache
2. **OS resolver cache** – If not found, it asks the OS resolver, which has its own cache
3. **Recursive resolver** (ISP / corporate / public DNS) – If the OS has no cached entry, it sends a recursive query to the configured DNS server (e.g., ISP DNS, 8.8.8.8, 1.1.1.1)
4. **Root servers** – If the resolver has no cache entry, it starts an iterative walk: asks a root server for the .com nameservers
5. **TLD (.com) servers** – Then it asks the .com TLD server for the facebook.com nameservers
6. **Authoritative servers** – Finally, it queries the authoritative DNS for facebook.com, which returns the A/AAAA records (IP addresses) for www.facebook.com
7. **Caching with TTL** – The recursive resolver and your OS cache the result for the record's TTL so future lookups are faster and don't hit the authoritative server until TTL expires

**Key phrasing:** "Client does one recursive query to its resolver; the resolver does iterative queries across root → TLD → authoritative."

## Recursive vs Iterative

- **Recursive query:** client says to the resolver, "Give me the final answer or an error," and the resolver does all the work
- **Iterative queries:** resolver asks upstream servers; each server either answers or says "ask that server next," and the resolver follows those referrals

## Production/SRE Considerations

- **DNS is a hard dependency** – If DNS fails or is misconfigured, your service can be completely unavailable even if the app and network are fine
- **TTL tuning** – Higher TTL reduces load and improves latency, but slows cutovers; lower TTL gives agility for failovers and migrations at the cost of more DNS traffic
- **Multiple A/AAAA records** – DNS can return multiple IPs and resolvers often use round-robin, which gives a simple form of load balancing and resilience
- **DNSSEC** – Adds integrity/authentication for DNS records, important for critical or security-sensitive services

### Real-World Example

AWS recently had a large outage where an internal DNS bug for the DynamoDB endpoint in us-east-1 broke name resolution, and because so many AWS services depend on that API, the DNS issue cascaded into a multi-hour, multi-service outage.

## Interview-Ready Answer

*When I hit www.facebook.com, the browser first checks its own DNS cache, then the OS cache. If there's no entry, the OS sends a recursive query to the configured DNS resolver, like an ISP or public DNS. That resolver either answers from its own cache or walks the hierarchy iteratively: it queries a root server to find the .com nameservers, then a .com TLD server to find the facebook.com nameservers, and finally the authoritative facebook.com DNS, which returns the IP address for www.facebook.com. That answer is cached at each layer for the TTL so subsequent lookups are fast.*

**Then a short production angle:**

*From a production point of view, DNS is a critical dependency: outages or bad records can take the whole service down. TTL values are a trade-off between performance and how quickly we can change records for failover. We often use multiple A or AAAA records for basic load balancing and may enable DNSSEC where integrity matters.*

---

# DNS Record Types

## Q5: What are the common DNS record types and their purposes?

| Record Type | Purpose | Example |
|-------------|---------|---------|
| **A** | IPv4 address mapping | www.facebook.com → 157.240.251.35 |
| **AAAA** | IPv6 address mapping | www.facebook.com → 2a03:2880:f12f:83:face:b00c::25de |
| **CNAME** | Canonical name (alias) | www.facebook.com → facebook.com |
| **MX** | Mail exchange with priority | facebook.com → 10 mx.facebook.com |
| **NS** | Name server records | facebook.com → ns1.facebook.com |
| **PTR** | Reverse DNS lookup | 157.240.251.35 → www.facebook.com |
| **TXT** | Text records | SPF, DKIM, domain verification |
| **SRV** | Service records | Port and protocol information |

## Production Uses

- **A/AAAA:** Load balancing with multiple IPs
- **CNAME:** CDN configurations, service aliases
- **MX:** Email routing and redundancy
- **TXT:** Security policies, domain ownership verification


---

# TLS Handshake

TLS is a security protocol that sits on top of TCP and protects data on the Internet.

The TLS handshake is the initial conversation where the browser and server agree how to protect the data and prove who the server is.

## How It Works

1. **The 'client hello' message:** The client initiates the handshake by sending a "hello" message to the server. Hello message includes: TLS version, list of cipher suites supported and a random byte known as 'client.random'

2. **The 'server hello' message:** In reply the server sends: server's SSL certificate with public key, chosen cipher suite and another random byte known as 'server.random'

3. **Authentication:** The client validates the server's SSL certificate with the CA that issues it. This confirms the client is interacting with the correct server

4. **Premaster secret:** Client sends another random byte known as premaster secret which is encrypted with the server's public key

5. **Decrypt premaster secret:** Server decrypts the premaster secret using the private key

6. **Session keys created:** Both client and server generate session keys using client random, server random and premaster secret

7. **Client ready:** Client sends Finished message encrypted with the session key

8. **Server ready:** Server sends Finished message encrypted with the session key

9. **Secure symmetric encryption achieved:** The handshake is completed and the communication continues using the session keys
---

# Complete Web Request Flow

## Q6: What happens when you type www.facebook.com in your browser?

### 1. URL Parsing & DNS Resolution

**Browser parses URL → Extracts hostname → DNS lookup process**

- Browser extracts protocol (https), hostname (www.facebook.com), and port (443)
- Initiates DNS resolution through browser cache → OS cache → recursive resolver → root/TLD/authoritative servers
- Multiple IP addresses returned for load balancing

### 2. TCP Connection Establishment

**Browser selects IP → Three-way handshake on port 443 (HTTPS)**

- Client sends SYN to selected IP address
- Server responds with SYN-ACK
- Client sends ACK
- Connection established

### 3. TLS Handshake (HTTPS)

**Client Hello (cipher suites, TLS version)**
- Client sends supported TLS versions and cipher suites, plus client.random

**Server Hello (selected cipher, certificate)**
- Server responds with chosen cipher suite, SSL certificate with public key, and server.random

**Certificate verification (chain of trust)**
- Client validates server certificate against trusted Certificate Authorities

**Key exchange and session establishment**
- Client sends premaster secret encrypted with server's public key
- Both sides generate session keys from client.random, server.random, and premaster secret
- Encrypted "Finished" messages exchanged to confirm secure channel

### 4. HTTP Request Formation

```
GET / HTTP/1.1
Host: www.facebook.com
User-Agent: Mozilla/5.0...
Accept: text/html,application/xhtml+xml
Accept-Encoding: gzip, deflate, br
Cookie: [session cookies]
```

- Browser constructs HTTP request with method, path, headers, and cookies
- Request sent over encrypted TLS connection

### 5. Server-Side Processing

**Load Balancer → Route request**
- Request hits load balancer which selects backend server based on algorithm (round-robin, least connections, etc.)

**Application Server → Process request**
- Application server receives request, authenticates user, executes business logic

**Database Queries → Generate response**
- Server queries databases, caches, and other services to build response

### 6. HTTP Response

```
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Encoding: gzip
Set-Cookie: [new cookies]
[HTML content]
```

- Server sends status code, headers, and compressed HTML content
- Response travels back through load balancer over encrypted connection

### 7. Browser Rendering

**HTML Parsing → DOM Construction**
- Browser parses HTML and builds Document Object Model (DOM) tree

**CSS Parsing → Styling**
- Browser parses CSS and builds CSSOM, applies styles to DOM

**JavaScript Execution**
- Browser executes JavaScript which may modify DOM/CSSOM

**Additional Resource Requests (images, CSS, JS)**
- Browser discovers and requests additional resources (may reuse existing TCP/TLS connections via HTTP keep-alive)
- Resources are fetched, processed, and rendered progressively
---

# API Performance Troubleshooting

## A user reports that accessing your company's API is slow. How do you troubleshoot this?

### Systematic Troubleshooting Approach

## 1. Clarify and Scope the Problem

**Who is affected:** all users or specific regions/ISPs/clients?

**What is affected:** all endpoints or specific ones?

**When did it start:** sudden vs gradual; correlate with deploys/changes

**How slow is "slow":** capture latency metrics (p50/p95/p99, TTFB, total time) and previous baseline

## 2. Network Layer Checks

From a reproducing client (or a close equivalent):

### Reachability and latency
```bash
ping api.company.com
```
- Basic reachability, RTT, packet loss

```bash
mtr api.company.com
```
- Find where along the path latency or loss appears

### DNS behavior
```bash
dig api.company.com
nslookup api.company.com
```
- Resolution time, expected IPs, TTLs, geo/routing issues

### Port connectivity
```bash
nc -zv api.company.com 443
telnet api.company.com 443
```
- Confirm TCP port reachability and any timeouts

**Document:** normal vs slow cases, RTT, loss, path differences, DNS answers, and port reachability

## 3. HTTP Timing with curl

Use curl to break down where time is spent:

```bash
curl -w "@curl-format.txt" -o /dev/null -s "https://api.company.com/endpoint"
```

**Key fields to log per run:**
- `time_namelookup` – DNS time
- `time_connect` – TCP connect time
- `time_appconnect` – TLS handshake time
- `time_starttransfer` – server processing + first byte time
- `time_total` – end-to-end time

Compare these between "good" and "slow" runs; note which phase is inflated

## 4. Server-Side Health and Logs

On API hosts (during slow periods if possible):

### System resources
```bash
top / htop
```
- CPU, load, memory

```bash
vmstat 1
iostat -x 1
```
- Memory pressure, I/O wait, disk saturation

### Network and sockets
```bash
iftop
```
- Per-host bandwidth usage

```bash
netstat -i
ss -tuln
```
- Interface stats, listening ports, connection counts/states

### Application logs
```bash
tail -f /var/log/application.log
grep "slow|timeout|error" /var/log/application.log
```
- Correlate slow periods with errors/timeouts/slow operations

**Document:** spikes in CPU, memory, I/O, connections, and any log events that match slow requests

## 5. Component-by-Component Analysis

Walk the full path:

- **Load balancer:** health checks, backend response times, error/timeout rates, connection distribution
- **Application servers:** CPU, GC, thread pools, connection pools, queueing or saturation
- **Database and other backends:** slow queries, locks, missing indexes, pool exhaustion
- **Internal network:** bandwidth utilization, packet loss on critical links

### Key Principle

Start broad (client + network), then follow the evidence inward (LB → app → DB), because "network-like" symptoms are often caused by overloaded application or database layers.
---

# vmstat - Virtual Memory Statistics

## Overview

vmstat (virtual memory statistics) is a Linux command-line tool that shows a compact, real-time snapshot of overall system health: processes, memory, swap, I/O, and CPU. It's one of the fastest ways to see if a box is CPU-bound, memory-pressured, or I/O-bound.

## Basic Usage and Behavior

**Command:** `vmstat [options] [delay [count]]`

- `vmstat` with no arguments: prints a single line of averaged stats since boot
- `vmstat 1`: prints a header, then a line every second; first line is "since boot", subsequent lines are per-interval stats
- Common pattern: `vmstat 1` or `vmstat 1 10` to watch the system for 10 seconds and see patterns

### Example Output

```bash
vmstat 1
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1  0      0 123456  7890 456789    0    0     1     2  100  200 10  5 80  5  0
```

## Column Breakdown

### procs: Process Run Queue and Blocking

**Columns:** `r`, `b`

- **r** – number of runnable processes (run queue length)
  - If r is consistently greater than the number of CPU cores, CPUs are likely saturated
  - Processes are waiting for CPU time

- **b** – number of processes in uninterruptible sleep (usually I/O wait)
  - If b is high and steady, many processes are blocked on disk or other I/O

**Use this to answer:** "Are we CPU-contended or stuck waiting on I/O?"

### memory: RAM Usage

**Columns:** `swpd`, `free`, `buff`, `cache`

- **swpd** – amount of memory used as swap (in KB)
  - Non-zero by itself isn't bad; watch if it grows and if swap-in/out (si, so) is active

- **free** – free, unused memory
  - On Linux this is often low because kernel uses free RAM for cache
  - Low free alone doesn't mean a problem

- **buff** – memory used for buffers (mainly metadata for block devices)

- **cache** – memory used for the page cache (file data cached in RAM)
  - Large cache is usually good; means kernel is caching disk reads

**Key insight:** low free + large cache is normal; high swap usage plus swap activity is concerning

### swap: Paging Activity

**Columns:** `si`, `so`

- **si** – swap in per second (KB/s): data moved from disk to RAM
- **so** – swap out per second (KB/s): data moved from RAM to disk

**Key interpretation:**
- Occasional, tiny si/so is usually fine
- Sustained non-zero si/so (especially dozens/hundreds of KB/s) indicates memory pressure and active paging
- High swap activity often correlates with high latency: processes stall waiting for pages from disk

### io: Block Device I/O

**Columns:** `bi`, `bo`

- **bi** – blocks received from a block device per second (read)
- **bo** – blocks sent to a block device per second (write)

These tell you "are we doing a lot of disk I/O right now?" but not which disk or process. Correlate with high `wa` (CPU I/O wait) to identify disk bottlenecks.

### system: Context Switches and Interrupts

**Columns:** `in`, `cs`

- **in** – interrupts per second
- **cs** – context switches per second

Very high cs can mean lots of threads/processes or a chatty workload causing frequent switches. Spikes in in/cs can accompany performance problems but are more of a "supporting signal."

### cpu: CPU Time Breakdown

**Columns:** `us`, `sy`, `id`, `wa`, `st`

- **us** – user time (%): CPU time spent running user processes
- **sy** – system time (%): time spent in kernel mode (syscalls, driver work, etc.)
- **id** – idle time (%): CPU not doing anything
- **wa** – I/O wait (%): CPU idle but waiting on I/O completion
- **st** – steal time (%): time "stolen" by hypervisor in virtualized environments

**Reading these:**
- **High us + low wa:** pure CPU-bound application work
- **High sy:** heavy kernel or syscall activity (networking, filesystem, context switches)
- **High wa:** system is I/O-bound; CPU mainly waiting on disk/network
- **High st:** on a VM, hypervisor is oversubscribed and your VM isn't getting enough physical CPU

## Practical Interpretation

**If r >> CPU cores and us+sy is high:** box is CPU-saturated

**If wa is high and b is high:** it's I/O-bound

**If si/so are high:** it's memory-pressured and swapping

## Delay and Count: Real-Time Monitoring

**Common ways to run vmstat:**

- `vmstat` – one report, averaged since boot (quick baseline but can hide spikes)
- `vmstat 1` – continuous, 1-second samples until Ctrl-C
- `vmstat 1 10` – 10 samples, 1 second apart

**Patterns matter more than a single line.** Look for:
- Columns that stay high or low over several seconds
- Changes that correlate with when the system "feels slow"
---

# High bi and bo in vmstat - What It Means and What to Do

## What bi and bo Indicate

In vmstat:

```bash
vmstat 1
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b swpd   free  buff  cache   si   so   bi   bo   in   cs us sy id wa st
 1  0    0 3750264 91344 1854024  0    0  156  245   89  142  2  1 97  0  0
```

- **bi:** blocks read from disk per second (blocks in)
- **bo:** blocks written to disk per second (blocks out)

Sustained high bi/bo values usually mean heavy disk I/O and a potential I/O bottleneck, especially if `wa` (I/O wait) is also high.

## Investigation Steps

### 1. Identify I/O Patterns

**Find which processes are generating disk I/O:**

```bash
iotop -ao
```
- Show processes with accumulated I/O over time

**Inspect per-device stats and I/O wait:**

```bash
iostat -x 1
```
- Extended stats for all devices

```bash
iostat -x sda 1
```
- Focus on a specific device (e.g., sda), check utilization, avg queue size, and latency

### 2. Analyze Possible Root Causes

**Check for memory pressure leading to swap I/O:**

```bash
free -h
```
- Overall memory and swap usage

```bash
swapon -s
```
- Active swap devices

```bash
cat /proc/meminfo
```
- Detailed memory metrics

**Look for processes doing heavy file operations:**

```bash
lsof +D /path/to/directory
```
- Open files under a directory

```bash
lsof | grep deleted
```
- Detect deleted but still-open files causing hidden disk usage

**Find large or growing files (logs, dumps, etc.):**

```bash
find /var/log -size +100M -ls
```
- Large log files

```bash
du -sh /* | sort -hr
```
- Top disk consumers at root

### 3. Consider Non-Obvious and Expected Causes

High I/O is not always a problem; it can be expected during:

- **Memory pressure → swapping** → high read/write I/O
- **Database maintenance jobs** (index rebuilds, vacuum/analyze)
- **Log rotation or compression** of large log files
- **Backup jobs** (file or snapshot backups)
- **Application patterns** such as poor DB queries or inefficient file access causing excessive disk reads/writes

## Key Point for Interviews

High bi/bo means the disks are busy, but that's only bad if it's unexpected or causing high latency. Always compare to baseline and correlate with I/O wait (wa), system load, and what the system is actually doing (cron jobs, DB tasks, backups, etc.).
---

# BGP - Border Gateway Protocol

## Overview

BGP is the Internet's routing protocol between large networks called Autonomous Systems (AS). It exchanges reachability for IP prefixes and lets each AS apply its own routing policies.

## Concise BGP Process

### 1. Session Setup

Routers in different ASes establish a TCP session (BGP peering) and become neighbors.

### 2. Prefix Announcement

Each AS advertises the IP prefixes it originates or can reach, along with attributes (AS-path, next-hop, local preference, MED, etc.).

### 3. Policy Application

Receiving routers apply local policies (filters, route-maps) to decide which routes to accept, prefer, or reject based on business and engineering goals.

### 4. Best-Path Selection

For each prefix, BGP runs a decision process: prefer highest local preference, then shortest AS-path, then other attributes (origin, MED, eBGP over iBGP, IGP cost, router ID tie-breaks).

### 5. Route Installation and Propagation

The chosen best path is installed into the routing table and then re-advertised to other BGP neighbors (subject to policy), allowing reachability information to spread across the Internet.

---

## Explain how BGP works and why it matters for a production engineer

### BGP Fundamentals

**BGP (Border Gateway Protocol):**
- Internet's routing protocol
- Path vector protocol (not just distance-based)
- Autonomous Systems (AS) announce IP prefixes
- Policy-based routing decisions

### How BGP Works

1. **Prefix Announcement:** AS announces IP prefixes it can reach
2. **Policy Application:** Neighbors receive announcements and apply routing policies
3. **Path Selection:** Best path chosen based on AS path length, local preference, etc.
4. **Route Propagation:** Selected routes advertised to other BGP neighbors

### Why Production Engineers Care

#### 1. Outage Impact

BGP issues can cause:
- **Route hijacking** (traffic sent to wrong destination)
- **Black-hole routing** (traffic dropped)
- **Suboptimal routing** (increased latency)
- **Complete connectivity loss**

#### 2. Multi-homing Benefits

**Multiple ISP Connections:**
- Redundancy for failover
- Load balancing across providers
- Better performance through path selection
- Requires BGP configuration knowledge

#### 3. CDN and Performance

- BGP affects which edge server users connect to
- Anycast routing relies on BGP for traffic distribution
- Understanding helps optimize content delivery

### Basic BGP Troubleshooting

**Check routing table:**
```bash
ip route show
route -n
```

**On BGP-enabled router:**
```bash
show ip bgp summary
show ip bgp neighbors
show ip route bgp
```

### Production Insight

You may not configure BGP daily, but understanding it helps diagnose mysterious connectivity issues and performance problems.
---

# Distance Vector vs Path Vector

## Distance Vector

"Routers exchange just distances to destinations and pick the shortest path; they don't know the full route, which makes it simpler but more prone to loops and slow convergence."

## Path Vector

"Routers exchange the full path plus attributes, so they can avoid loops and make policy-based decisions; BGP uses this model between Autonomous Systems on the Internet."
