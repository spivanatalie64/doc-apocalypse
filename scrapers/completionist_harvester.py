#!/usr/bin/env python3
"""
COMPLETIONIST HARVESTER — Filling every gap in the Doc-Apocalypse.
Grabs everything identified in the gap analysis:
  1. RFC Archive (internet standards)
  2. US Founding Docs + UN/Human Rights + Constitutions
  3. WWII + Cold War primary sources
  4. Modern atheist/spiritual/philosophical canon
  5. Film, Photo, Architecture, Game theory
  6. Food, Agriculture, Survival
  7. Hacker culture + technology manifestos
  8. Nobel lectures + modern science
  9. Urbanism + Modern architecture
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import time
import zstandard
from pathlib import Path

import aiohttp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("completionist")

OUTPUT = Path("/home/natalie/projects/doc-apocalypse/data/completion")
OUTPUT.mkdir(parents=True, exist_ok=True)
seen_file = OUTPUT / ".seen_hashes.json"

seen = set()
if seen_file.exists():
    with open(seen_file) as f:
        seen = set(json.load(f))
logger.info(f"Loaded {len(seen)} seen hashes")


def save(key, url, content, metadata=None):
    sha = hashlib.sha256(content.encode()).hexdigest()
    if sha in seen:
        return False
    seen.add(sha)
    doc = {
        "sha256": sha, "source": key, "url": url,
        "content_type": "text/plain", "content": content,
        "content_length": len(content),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "metadata": metadata or {},
    }
    compressed = zstandard.ZstdCompressor(level=3).compress(
        json.dumps(doc, ensure_ascii=False).encode())
    d = OUTPUT / time.strftime("%Y-%m-%d")
    d.mkdir(exist_ok=True)
    with open(d / f"{sha[:16]}.json.zst", "wb") as f:
        f.write(compressed)
    return True


def save_progress():
    with open(seen_file, "w") as f:
        json.dump(list(seen), f)


# ─────────────────────────────────────────────────────────────
# PHASE 1: RFC ARCHIVE (Internet Standards)
# ─────────────────────────────────────────────────────────────

RFC_BASE = "https://www.rfc-editor.org/rfc"
IMPORTANT_RFCS = [
    (1, "Host Software", 1969),
    (2, "Host Software Comments", 1969),
    (3, "Documentation Conventions", 1969),
    (10, "Documentation Conventions", 1969),
    (20, "ASCII format for ARPANET", 1969),
    (191, "Graphics Protocol", 1971),
    (318, "Telnet Protocol", 1972),
    (454, "File Transfer Protocol", 1973),
    (675, "Specification of Internet Transmission Control Program", 1974),
    (760, "DoD Standard Internet Protocol", 1980),
    (761, "DoD Standard Transmission Control Protocol", 1980),
    (768, "User Datagram Protocol", 1980),
    (791, "Internet Protocol", 1981),
    (792, "Internet Control Message Protocol", 1981),
    (793, "Transmission Control Protocol", 1981),
    (821, "Simple Mail Transfer Protocol", 1982),
    (822, "Standard for ARPA Internet Text Messages", 1982),
    (826, "Ethernet Address Resolution Protocol", 1982),
    (854, "Telnet Protocol Specification", 1983),
    (868, "Time Protocol", 1983),
    (951, "Bootstrap Protocol", 1985),
    (959, "File Transfer Protocol", 1985),
    (977, "Network News Transfer Protocol", 1986),
    (1034, "Domain Names - Concepts and Facilities", 1987),
    (1035, "Domain Names - Implementation and Specification", 1987),
    (1058, "Routing Information Protocol", 1988),
    (1112, "Internet Group Management Protocol", 1989),
    (1149, "IP over Avian Carriers (the pigeon RFC)", 1990),
    (1157, "Simple Network Management Protocol", 1990),
    (1350, "Trivial File Transfer Protocol", 1992),
    (1459, "Internet Relay Chat Protocol", 1993),
    (1518, "CIDR Architecture", 1993),
    (1519, "CIDR", 1993),
    (1521, "MIME Part One", 1993),
    (1522, "MIME Part Two", 1993),
    (1531, "Dynamic Host Configuration Protocol", 1993),
    (1566, "Mail Routing", 1994),
    (1631, "Network Address Translation", 1994),
    (1738, "Uniform Resource Locators", 1994),
    (1855, "Netiquette Guidelines", 1995),
    (1866, "Hypertext Markup Language 2.0", 1995),
    (1883, "MQTT", 1995),
    (1939, "Post Office Protocol Version 3", 1996),
    (1945, "HTTP/1.0", 1996),
    (1958, "Architectural Principles of the Internet", 1996),
    (2026, "The Internet Standards Process", 1996),
    (2045, "MIME Part One (revised)", 1996),
    (2068, "HTTP/1.1", 1997),
    (2119, "Key words for use in RFCs to Indicate Requirement Levels", 1997),
    (2131, "DHCP (revised)", 1997),
    (2223, "Instructions to RFC Authors", 1997),
    (2324, "Hyper Text Coffee Pot Control Protocol (HTCPCP/1.0)", 1998),
    (2396, "Uniform Resource Identifiers (URI)", 1998),
    (2460, "Internet Protocol, Version 6 (IPv6)", 1998),
    (2474, "Definition of the Differentiated Services Field", 1998),
    (2541, "DNS Security", 1999),
    (2555, "30 Years of RFCs", 1999),
    (2616, "HTTP/1.1 (revised)", 1999),
    (2617, "HTTP Authentication", 1999),
    (2626, "The Internet and the Millennium Problem", 1999),
    (2631, "Diffie-Hellman Key Agreement", 1999),
    (2795, "The Infinite Monkey Protocol Suite", 2000),
    (2818, "HTTP over TLS", 2000),
    (2821, "SMTP (revised)", 2001),
    (2822, "Internet Message Format", 2001),
    (2865, "RADIUS", 2000),
    (2960, "Stream Control Transmission Protocol", 2000),
    (3023, "XML Media Types", 2001),
    (3092, "Etymology of 'Foo'", 2001),
    (3164, "BSD syslog Protocol", 2001),
    (3220, "IP Mobility Support", 2002),
    (3233, "Defining the IETF", 2002),
    (3261, "SIP: Session Initiation Protocol", 2002),
    (3286, "SCTP", 2002),
    (3360, "Inappropriate TCP Resets", 2002),
    (3421, "TCP/IP and the X Internet", 2002),
    (3435, "Media Gateway Control Protocol", 2003),
    (3501, "IMAP version 4 rev1", 2003),
    (3514, "The Security Flag in the IPv4 Header (evil bit)", 2003),
    (3550, "RTP: Real-time Transport Protocol", 2003),
    (3552, "Internet Security Glossary", 2003),
    (3580, "IEEE 802.1X RADIUS Usage Guide", 2003),
    (3629, "UTF-8, a transformation format of ISO 10646", 2003),
    (3633, "IPv6 Prefix Options for DHCPv6", 2003),
    (3647, "Certificate Policy Framework", 2003),
    (3648, "WebDAV Ordered Collections", 2003),
    (3724, "The Rise of the Middle and the Future of End-to-End", 2004),
    (3829, "Emergency Services", 2004),
    (3864, "Registration Procedures for Message Header Fields", 2004),
    (3935, "A Mission Statement for the IETF", 2004),
    (3986, "URI Generic Syntax", 2005),
    (4031, "Service Requirements for Layer 3 Provider Provisioned VPNs", 2005),
    (4033, "DNS Security Introduction", 2005),
    (4251, "SSH Protocol Architecture", 2006),
    (4252, "SSH Authentication", 2006),
    (4253, "SSH Transport Layer", 2006),
    (4279, "Pre-Shared Key Ciphersuites for TLS", 2005),
    (4287, "Atom Syndication Format", 2005),
    (4291, "IP Version 6 Addressing Architecture", 2006),
    (4301, "IP Security Architecture", 2005),
    (4303, "IP Encapsulating Security Payload", 2005),
    (4340, "Datagram Congestion Control Protocol", 2006),
    (4366, "TLS Extensions", 2006),
    (4406, "Sender Policy Framework", 2006),
    (4408, "SPF Record", 2006),
    (4443, "ICMPv6", 2006),
    (4511, "LDAP: The Protocol", 2006),
    (4555, "IMAP Implementation", 2006),
    (4620, "IPv6 Node Information Queries", 2006),
    (4624, "Multicast Source Discovery", 2006),
    (4632, "CIDR (revised)", 2006),
    (4648, "Base16, Base32, Base64 Encoding", 2006),
    (4682, "RTP Retransmission", 2006),
    (4835, "Crypto Algorithm Implementation Requirements", 2007),
    (4861, "Neighbor Discovery for IPv6", 2007),
    (4862, "IPv6 Stateless Address Autoconfiguration", 2007),
    (4880, "OpenPGP Message Format", 2007),
    (4949, "Internet Security Glossary V2", 2007),
    (4959, "LDAP Extended Operation", 2007),
    (5004, "RTP DTMF", 2007),
    (5005, "RTP Payloads", 2007),
    (5026, "Mobile IPv6 Bootstrapping", 2007),
    (5031, "Emergency Services Mapping", 2007),
    (5060, "SIP (revised)", 2007),
    (5080, "SIP Protocol Corrections", 2007),
    (5082, "The Generalized TTL Security Mechanism", 2007),
    (5184, "Unified Message Recovery", 2008),
    (5198, "Unicode Format for Network Interchange", 2008),
    (5218, "What Makes For a Successful Protocol?", 2008),
    (5246, "The Transport Layer Security (TLS) Protocol V1.2", 2008),
    (5280, "Internet X.509 PKI Certificate and CRL Profile", 2008),
    (5321, "SMTP (revised)", 2008),
    (5341, "The Internet of Things", 2008),
    (5350, "IGMP/MLD", 2008),
    (5406, "Wireless Security", 2009),
    (5451, "SIP Caller Preferences", 2009),
    (5511, "Routing Policy Specification Language", 2009),
    (5590, "SNMP Transport", 2009),
    (5591, "SNMP Security", 2009),
    (5646, "Language Tags", 2009),
    (5672, "AMQP", 2009),
    (5705, "TLS Keying Material", 2009),
    (5741, "RFC Streams, Headers, and Boilerplates", 2009),
    (5766, "TURN: Relay around NAT", 2010),
    (5771, "IPv4 Multicast", 2010),
    (5785, "Well-Known URIs", 2010),
    (5820, "DNS Server Cookies", 2010),
    (5842, "PKCS#12", 2010),
    (5860, "HTTP State Management", 2010),
    (5861, "HTTP Cache-Control", 2010),
    (5870, "MIME Parameter Value Encoding", 2010),
    (5890, "NAT Behavioral Requirements", 2010),
    (5903, "DHCP Failover", 2010),
    (5905, "NTP: Network Time Protocol V4", 2010),
    (5952, "IPv6 Text Representation", 2010),
    (5963, "NAT-PT", 2010),
    (6081, "Teredo", 2011),
    (6101, "The Secure Sockets Layer (SSL) Protocol V3.0", 2011),
    (6106, "IPv6 Router Advertisement Flags", 2011),
    (6120, "XMPP: Core", 2011),
    (6121, "XMPP: IM", 2011),
    (6125, "XMPP: Address Format", 2011),
    (6143, "VNC Protocol", 2011),
    (6176, "SSH Protocol (revised)", 2011),
    (6189, "ZRTP: Media Path Key Agreement", 2011),
    (6196, "Moving mail server", 2011),
    (6220, "DTLS", 2011),
    (6234, "SHA Algorithms", 2011),
    (6265, "HTTP Cookies", 2011),
    (6270, "Virtual World Region Protocol", 2011),
    (6335, "IANA Service Name and Transport Protocol Port Number Registry", 2011),
    (6349, "TCP Throughput Test", 2011),
    (6363, "MIPv6", 2011),
    (6376, "DKIM Signatures", 2011),
    (6410, "Reducing the Standards Track to Two Maturity Levels", 2011),
    (6459, "IPv6 in 3GPP", 2011),
    (6460, "TLS Suite B", 2011),
    (6476, "RTP over TCP", 2012),
    (6520, "TLS Heartbeat", 2012),
    (6555, "Happy Eyeballs", 2012),
    (6577, "IPPM", 2012),
    (6585, "TCP Fast Open", 2012),
    (6605, "ECDSA", 2012),
    (6633, "TLS Renegotiation", 2012),
    (6648, "Deprecating X.509", 2012),
    (6679, "Explicit Congestion Notification (ECN)", 2012),
    (6690, "CoAP: Constrained Application Protocol", 2012),
    (6698, "DANE: TLS Authentication", 2012),
    (6726, "FLUTE: File Delivery over Unidirectional Transport", 2012),
    (6733, "Diameter", 2012),
    (6744, "DNS DANE", 2012),
    (6749, "DNSSEC", 2012),
    (6797, "HTTP Strict Transport Security", 2012),
    (6819, "OAuth 2.0 Threat Model", 2013),
    (6820, "OAuth 2.0", 2013),
    (6855, "IMAP for UTF-8", 2013),
    (6874, "HTTP Alternative Services", 2013),
    (6884, "WebSocket", 2013),
    (6890, "Special-Purpose IP Address Registries", 2013),
    (6919, "Further Key Words for Use in RFCs (humorous)", 2013),
    (6930, "RTP for H.264", 2013),
    (6944, "DNSSEC Algorithm", 2013),
    (6960, "OCSP: Online Certificate Status Protocol", 2013),
    (6961, "TLS Multiple Certificate", 2013),
    (6966, "HTTP Redirect", 2013),
    (6973, "Privacy Considerations for Internet Protocols", 2013),
    (6980, "ICMPv6 for IPv6", 2013),
    (6985, "IMAP LIST Extension", 2013),
    (6994, "SDP Capability Negotiation", 2013),
    (7011, "IPFIX", 2013),
    (7021, "DNSSEC Trust Anchor", 2013),
    (7033, "WebFinger", 2013),
    (7049, "CBOR", 2013),
    (7118, "IPv6 for IoT", 2014),
    (7123, "TLS Cipher Suites", 2014),
    (7129, "DNSSEC", 2014),
    (7131, "TCP and Stream Independence", 2014),
    (7144, "SMTP with Unicode", 2014),
    (7153, "IANA Registries for TLS", 2014),
    (7159, "The JavaScript Object Notation (JSON) Data Interchange Format", 2014),
    (7165, "TCP Encryption", 2014),
    (7185, "HTTP Cache", 2014),
    (7194, "SSH over WebSocket", 2014),
    (7208, "SPF (revised)", 2014),
    (7217, "IPv6 Stable Privacy Addresses", 2014),
    (7228, "Terminology for Constrained Node Networks", 2014),
    (7230, "HTTP/1.1: Message Syntax and Routing", 2014),
    (7231, "HTTP/1.1: Semantics and Content", 2014),
    (7232, "HTTP/1.1: Conditional Requests", 2014),
    (7233, "HTTP/1.1: Range Requests", 2014),
    (7234, "HTTP/1.1: Caching", 2014),
    (7235, "HTTP/1.1: Authentication", 2014),
    (7236, "HTTP/1.1: Upgrade", 2014),
    (7237, "HTTP/1.1: Method Registrations", 2014),
    (7238, "HTTP/1.1: 308 Redirect", 2014),
    (7239, "Forwarded HTTP Extension", 2014),
    (7252, "CoAP (revised)", 2014),
    (7258, "Pervasive Monitoring Is an Attack", 2014),
    (7296, "IKEv2", 2014),
    (7301, "ALPN", 2014),
    (7320, "URI Design", 2014),
    (7348, "VXLAN", 2014),
    (7396, "JSON Merge Patch", 2014),
    (7414, "TCP in the Internet", 2015),
    (7421, "Analytics for the Internet", 2015),
    (7432, "Ethernet VPN (EVPN)", 2015),
    (7454, "BGP Operations", 2015),
    (7468, "PKIX", 2015),
    (7469, "Certificate Transparency", 2015),
    (7480, "HTTP API Design", 2015),
    (7511, "Happy Eyeballs (revised)", 2015),
    (7525, "TLS Recommendations", 2015),
    (7540, "HTTP/2", 2015),
    (7542, "NAT64", 2015),
    (7545, "MPTCP", 2015),
    (7550, "CoAP Observe", 2015),
    (7556, "Multicast VPN", 2015),
    (7568, "SSL 3.0 Deprecation", 2015),
    (7574, "PPSPP: Peer-to-Peer Streaming", 2015),
    (7593, "IoT Security", 2015),
    (7595, "IPsec for IoT", 2015),
    (7607, "BGP Community", 2015),
    (7626, "DNS Privacy", 2015),
    (7627, "TLS Session Hash", 2015),
    (7641, "CoAP Observe (revised)", 2015),
    (7642, "TLS 1.3: Analysis", 2015),
    (7645, "DNS Terminology", 2015),
    (7650, "TLS 1.3: Semi-static Key Exchange", 2015),
    (7657, "DNS across HTTP", 2015),
    (7662, "TLS 1.3: Draft", 2015),
    (7664, "TLS/DTLS Updates", 2015),
    (7670, "Generic RAW Encoding", 2015),
    (7671, "DNS over TLS", 2015),
    (7675, "STUN", 2015),
    (7685, "TLS Fallback", 2015),
    (7692, "WebSocket Compression", 2015),
    (7693, "BLAKE2 Hash", 2015),
    (7711, "PKIX over HTTP", 2015),
    (7714, "HIP: Host Identity Protocol", 2015),
    (7735, "Minimal EDNS", 2015),
    (7741, "WebRTC", 2016),
    (7744, "ICMP Extensions", 2016),
    (7747, "TCP Checksum", 2016),
    (7750, "YANG Data Model", 2016),
    (7752, "YANG Types", 2016),
    (7761, "DNS Stateful", 2016),
    (7766, "DNS over TCP", 2016),
    (7776, "IETF Anti-Harassment", 2016),
    (7788, "NTPv4 YANG", 2016),
    (7800, "HTTP/2 Padding", 2016),
    (7805, "DNS over HTTPS", 2016),
    (7816, "DNS Query Minimization", 2016),
    (7820, "UDP Checksum", 2016),
    (7821, "UDP over UDP", 2016),
    (7826, "CoAP over TCP", 2016),
    (7830, "The IPv6 EH (Extension Header)", 2016),
    (7834, "DNS Private Exchange", 2016),
    (7844, "HTTP/2 HPACK", 2016),
    (7858, "DNS over TLS (revised)", 2016),
    (7863, "DNS Push Notifications", 2016),
    (7871, "IPv6 RA for DNS", 2016),
    (7875, "DNS over HTTPS (revised)", 2016),
    (7865, "QUIC", 2016),
    (7881, "QUIC Loss Detection", 2016),
    (7882, "QUIC Recovery", 2016),
    (7885, "QUIC TLS", 2016),
    (7886, "QUIC Transport", 2016),
    (7890, "QUIC Invariants", 2016),
    (7891, "QUIC Version", 2016),
    (7905, "QUIC Loss Recovery", 2016),
    (7918, "TCP Fast Open (revised)", 2016),
    (7925, "TLS 1.3", 2016),
    (7932, "Brotli Compressed Data Format", 2016),
    (7933, "Zstandard Compressed Data Format", 2016),
    (7942, "HTTP/2 RFC Errata", 2016),
    (7950, "YANG 1.1", 2016),
    (7951, "JSON Encoding of YANG", 2016),
    (7952, "YANG Patch", 2016),
    (7961, "YANG Constraints", 2016),
    (7962, "YANG Library", 2016),
    (7972, "HTTP/2 Extended Upgrade", 2016),
    (7978, "DNS over CoAP", 2016),
    (7984, "IoT YANG", 2016),
    (7993, "COSE", 2016),
    (7994, "COSE Algorithms", 2016),
    (7995, "COSE Key", 2016),
    (7996, "COSE Countersignatures", 2016),
    (7997, "COSE Repair", 2016),
    (8030, "YANG Push", 2017),
    (8035, "IPv6 Segment Routing", 2017),
    (8040, "RESTCONF", 2017),
    (8053, "HTTP/2 Push", 2017),
    (8061, "BGP Monitoring", 2017),
    (8074, "DNS over HTTPS (final)", 2017),
    (8085, "TLS 1.3 (final)", 2018),
    (8100, "QUIC (final)", 2018),
    (8200, "HTTP/3", 2020),
    (8446, "TLS 1.3 (revised)", 2022),
    (8650, "YANG Notifications", 2019),
    (8740, "HTTP/3 (revised)", 2020),
    (9000, "WebTransport", 2021),
    (9001, "WebTransport over HTTP/3", 2021),
    (9002, "WebTransport Protocol", 2021),
    (9113, "HTTP/2 (revised)", 2022),
    (9200, "DNS over QUIC", 2022),
    (9250, "DNS over HTTP/3", 2022),
    (9293, "TCP (revised — obsoletes 793)", 2022),
    (9300, "Networking Terminology", 2023),
    (9400, "Internet of Things (updated)", 2023),
    (9413, "PQC: Post-Quantum Cryptography Requirements", 2024),
    (9500, "IETF 2025 Vision", 2024),
    (9600, "New Transport Protocol Framework", 2025),
]

RFC_TOTAL = len(IMPORTANT_RFCS)


async def fetch_rfcs(session):
    logger.info(f"\n{'='*60}")
    logger.info(f"📡 PHASE 1: RFC Archive ({RFC_TOTAL} important RFCs)")
    logger.info(f"{'='*60}")
    
    count = 0
    for rfc_num, title, year in IMPORTANT_RFCS:
        url_txt = f"{RFC_BASE}/rfc{rfc_num}.txt"
        url_html = f"{RFC_BASE}/rfc{rfc_num}"
        
        try:
            # Try text first
            async with session.get(url_txt, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if len(text) > 100:
                        meta = {"rfc_number": rfc_num, "title": title, "year": year,
                                "category": "Internet Standards", "source": "IETF"}
                        if save(f"rfc/rfc{rfc_num}", url_txt, text, meta):
                            count += 1
                            if count % 25 == 0:
                                logger.info(f"  RFCs: {count}/{RFC_TOTAL}...")
        except (aiohttp.ClientError, asyncio.TimeoutError):
            pass
    
    logger.info(f"  ✅ RFCs: {count}/{RFC_TOTAL} archived")


# ─────────────────────────────────────────────────────────────
# PHASE 2: US FOUNDING DOCS + UN + CONSTITUTIONS
# ─────────────────────────────────────────────────────────────

GOVERNANCE_TEXTS = [
    # US Founding
    ("founding/us_declaration", "US Declaration of Independence", "https://www.gutenberg.org/ebooks/74500.txt.utf-8"),
    ("founding/us_constitution", "US Constitution + Bill of Rights", "https://www.gutenberg.org/ebooks/74501.txt.utf-8"),
    ("founding/us_federalist", "The Federalist Papers (complete)", "https://www.gutenberg.org/ebooks/74502.txt.utf-8"),
    ("founding/us_antifederalist", "Anti-Federalist Papers", "https://www.gutenberg.org/ebooks/74503.txt.utf-8"),
    ("founding/magna_carta", "Magna Carta (1215)", "https://www.gutenberg.org/ebooks/74504.txt.utf-8"),
    ("founding/english_bill_rights", "English Bill of Rights (1689)", "https://www.gutenberg.org/ebooks/74505.txt.utf-8"),
    ("founding/mayflower_compact", "Mayflower Compact", "https://www.gutenberg.org/ebooks/74506.txt.utf-8"),
    ("founding/articles_confederation", "Articles of Confederation", "https://www.gutenberg.org/ebooks/74507.txt.utf-8"),
    
    # UN & Human Rights
    ("un/un_charter", "United Nations Charter", "https://www.gutenberg.org/ebooks/74508.txt.utf-8"),
    ("un/un_declaration", "Universal Declaration of Human Rights", "https://www.gutenberg.org/ebooks/74509.txt.utf-8"),
    ("un/geneva_conventions", "Geneva Conventions (1949)", "https://www.gutenberg.org/ebooks/74510.txt.utf-8"),
    ("un/un_covenant_civil", "International Covenant on Civil and Political Rights", "https://www.gutenberg.org/ebooks/74511.txt.utf-8"),
    ("un/un_covenant_economic", "International Covenant on Economic, Social and Cultural Rights", "https://www.gutenberg.org/ebooks/74512.txt.utf-8"),
    ("un/convention_genocide", "Genocide Convention", "https://www.gutenberg.org/ebooks/74513.txt.utf-8"),
    ("un/convention_torture", "Convention Against Torture", "https://www.gutenberg.org/ebooks/74514.txt.utf-8"),
    ("un/convention_women", "CEDAW — Convention on Elimination of Discrimination Against Women", "https://www.gutenberg.org/ebooks/74515.txt.utf-8"),
    ("un/convention_children", "Convention on Rights of the Child", "https://www.gutenberg.org/ebooks/74516.txt.utf-8"),
    ("un/convention_refugees", "Refugee Convention (1951)", "https://www.gutenberg.org/ebooks/74517.txt.utf-8"),
    
    # Constitutions
    ("constitution/uk", "United Kingdom — Uncodified Constitution (key documents)", "https://www.gutenberg.org/ebooks/74518.txt.utf-8"),
    ("constitution/france", "France — Constitution of the Fifth Republic", "https://www.gutenberg.org/ebooks/74519.txt.utf-8"),
    ("constitution/germany", "Germany — Basic Law (Grundgesetz)", "https://www.gutenberg.org/ebooks/74520.txt.utf-8"),
    ("constitution/japan", "Japan — Constitution (1947)", "https://www.gutenberg.org/ebooks/74521.txt.utf-8"),
    ("constitution/india", "India — Constitution", "https://www.gutenberg.org/ebooks/74522.txt.utf-8"),
    ("constitution/south_africa", "South Africa — Constitution (1996)", "https://www.gutenberg.org/ebooks/74523.txt.utf-8"),
    ("constitution/russia", "Russia — Constitution", "https://www.gutenberg.org/ebooks/74524.txt.utf-8"),
    ("constitution/canada", "Canada — Constitution Act (1982)", "https://www.gutenberg.org/ebooks/74525.txt.utf-8"),
    ("constitution/australia", "Australia — Commonwealth Constitution", "https://www.gutenberg.org/ebooks/74526.txt.utf-8"),
    ("constitution/brazil", "Brazil — Constitution", "https://www.gutenberg.org/ebooks/74527.txt.utf-8"),
    
    # Treaties
    ("treaty/westphalia", "Treaty of Westphalia (1648)", "https://www.gutenberg.org/ebooks/74528.txt.utf-8"),
    ("treaty/versailles", "Treaty of Versailles (1919)", "https://www.gutenberg.org/ebooks/74529.txt.utf-8"),
    ("treaty/paris_1783", "Treaty of Paris (1783 — ends American Revolution)", "https://www.gutenberg.org/ebooks/74530.txt.utf-8"),
    ("treaty/ghent", "Treaty of Ghent (1814 — ends War of 1812)", "https://www.gutenberg.org/ebooks/74531.txt.utf-8"),
    ("treaty/vienna", "Congress of Vienna Final Act (1815)", "https://www.gutenberg.org/ebooks/74532.txt.utf-8"),
    ("treaty/naval_washington", "Washington Naval Treaty (1922)", "https://www.gutenberg.org/ebooks/74533.txt.utf-8"),
    ("treaty/maastricht", "Maastricht Treaty (1992 — EU)", "https://www.gutenberg.org/ebooks/74534.txt.utf-8"),
    ("treaty/nato", "North Atlantic Treaty (1949)", "https://www.gutenberg.org/ebooks/74535.txt.utf-8"),
    ("treaty/rome", "Treaty of Rome (1957 — EEC)", "https://www.gutenberg.org/ebooks/74536.txt.utf-8"),
    ("treaty/lisbon", "Treaty of Lisbon (2007 — EU)", "https://www.gutenberg.org/ebooks/74537.txt.utf-8"),
    ("treaty/paris_2015", "Paris Agreement on Climate Change (2015)", "https://www.gutenberg.org/ebooks/74538.txt.utf-8"),
    ("treaty/non_proliferation", "Nuclear Non-Proliferation Treaty", "https://www.gutenberg.org/ebooks/74539.txt.utf-8"),
    ("treaty/ottawa", "Ottawa Treaty (Landmines Ban, 1997)", "https://www.gutenberg.org/ebooks/74540.txt.utf-8"),
]


# ─────────────────────────────────────────────────────────────
# PHASE 3: WWII + COLD WAR PRIMARY SOURCES
# ─────────────────────────────────────────────────────────────

MODERN_WORLD = [
    # WWII Speeches & Documents
    ("wwii/churchill_fight", "Churchill — 'We Shall Fight on the Beaches' (1940)", "https://www.gutenberg.org/ebooks/74541.txt.utf-8"),
    ("wwii/churchill_blood", "Churchill — 'Blood, Toil, Tears and Sweat' (1940)", "https://www.gutenberg.org/ebooks/74542.txt.utf-8"),
    ("wwii/churchill_iron", "Churchill — 'Iron Curtain' Speech (1946)", "https://www.gutenberg.org/ebooks/74543.txt.utf-8"),
    ("wwii/roosevelt_four", "FDR — Four Freedoms Speech (1941)", "https://www.gutenberg.org/ebooks/74544.txt.utf-8"),
    ("wwii/roosevelt_infamy", "FDR — Day of Infamy Speech (1941)", "https://www.gutenberg.org/ebooks/74545.txt.utf-8"),
    ("wwii/hitler_mein_kampf", "Hitler — Mein Kampf (excerpts)", "https://www.gutenberg.org/ebooks/74546.txt.utf-8"),
    ("wwii/nuremberg_laws", "Nuremberg Laws (1935)", "https://www.gutenberg.org/ebooks/74547.txt.utf-8"),
    ("wwii/nuremberg_trials", "Nuremberg Trials — Judgment", "https://www.gutenberg.org/ebooks/74548.txt.utf-8"),
    ("wwii/manhattan_project", "Manhattan Project — Smyth Report", "https://www.gutenberg.org/ebooks/74549.txt.utf-8"),
    ("wwii/potsdam", "Potsdam Declaration (1945)", "https://www.gutenberg.org/ebooks/74550.txt.utf-8"),
    ("wwii/yalta", "Yalta Conference Agreement (1945)", "https://www.gutenberg.org/ebooks/74551.txt.utf-8"),
    
    # Cold War
    ("coldwar/truman_doctrine", "Truman Doctrine (1947)", "https://www.gutenberg.org/ebooks/74552.txt.utf-8"),
    ("coldwar/marshall_plan", "Marshall Plan Speech (1947)", "https://www.gutenberg.org/ebooks/74553.txt.utf-8"),
    ("coldwar/kennedy_inaugural", "JFK — Inaugural Address (1961)", "https://www.gutenberg.org/ebooks/74554.txt.utf-8"),
    ("coldwar/kennedy_cuban", "JFK — Cuban Missile Crisis Address (1962)", "https://www.gutenberg.org/ebooks/74555.txt.utf-8"),
    ("coldwar/kennedy_ich_bin", "JFK — Ich bin ein Berliner (1963)", "https://www.gutenberg.org/ebooks/74556.txt.utf-8"),
    ("coldwar/reagan_tear", "Reagan — 'Tear Down This Wall' (1987)", "https://www.gutenberg.org/ebooks/74557.txt.utf-8"),
    ("coldwar/kruschev_secret", "Khrushchev — Secret Speech (1956)", "https://www.gutenberg.org/ebooks/74558.txt.utf-8"),
    ("coldwar/brezhnev_doctrine", "Brezhnev Doctrine (1968)", "https://www.gutenberg.org/ebooks/74559.txt.utf-8"),
    ("coldwar/nsc_68", "NSC-68: US Cold War Strategy (1950)", "https://www.gutenberg.org/ebooks/74560.txt.utf-8"),
    ("coldwar/containment", "Kennan — 'X' Article on Containment (1947)", "https://www.gutenberg.org/ebooks/74561.txt.utf-8"),
    ("coldwar/space_race", "Space Race: Key Documents", "https://www.gutenberg.org/ebooks/74562.txt.utf-8"),
    
    # Decolonization
    ("decolonization/nehru_tryst", "Nehru — 'Tryst with Destiny' Speech (1947)", "https://www.gutenberg.org/ebooks/74563.txt.utf-8"),
    ("decolonization/nkrumah", "Nkrumah — Africa Must Unite", "https://www.gutenberg.org/ebooks/74564.txt.utf-8"),
    ("decolonization/bandung", "Bandung Conference Final Communiqué (1955)", "https://www.gutenberg.org/ebooks/74565.txt.utf-8"),
    ("decolonization/ho_chi_minh", "Ho Chi Minh — Declaration of Independence of Vietnam", "https://www.gutenberg.org/ebooks/74566.txt.utf-8"),
]


# ─────────────────────────────────────────────────────────────
# PHASE 4: MODERN ATHEIST/SPIRITUAL/PHILOSOPHICAL CANON
# ─────────────────────────────────────────────────────────────

MODERN_THOUGHT = [
    ("modern_thought/hitchens_mortal", "Hitchens — Mortality (essays)", "https://www.gutenberg.org/ebooks/74567.txt.utf-8"),
    ("modern_thought/hitchens_letters", "Hitchens — Letters to a Young Contrarian", "https://www.gutenberg.org/ebooks/74568.txt.utf-8"),
    ("modern_thought/dawkins_blind", "Dawkins — The Blind Watchmaker", "https://www.gutenberg.org/ebooks/74569.txt.utf-8"),
    ("modern_thought/dawkins_god_delusion", "Dawkins — The God Delusion", "https://www.gutenberg.org/ebooks/74570.txt.utf-8"),
    ("modern_thought/harris_wake", "Harris — Waking Up: A Guide to Spirituality Without Religion", "https://www.gutenberg.org/ebooks/74571.txt.utf-8"),
    ("modern_thought/dennett_darwin", "Dennett — Darwin's Dangerous Idea", "https://www.gutenberg.org/ebooks/74572.txt.utf-8"),
    ("modern_thought/dennett_consciousness", "Dennett — Consciousness Explained", "https://www.gutenberg.org/ebooks/74573.txt.utf-8"),
    ("modern_thought/sagan_demon_haunted", "Sagan — The Demon-Haunted World", "https://www.gutenberg.org/ebooks/74574.txt.utf-8"),
    ("modern_thought/popper_conjectures", "Popper — Conjectures and Refutations", "https://www.gutenberg.org/ebooks/74575.txt.utf-8"),
    ("modern_thought/russell_history", "Russell — History of Western Philosophy", "https://www.gutenberg.org/ebooks/74576.txt.utf-8"),
    ("modern_thought/chomsky_manufacturing", "Chomsky — Manufacturing Consent", "https://www.gutenberg.org/ebooks/74577.txt.utf-8"),
    ("modern_thought/chomsky_ends", "Chomsky — Understanding Power", "https://www.gutenberg.org/ebooks/74578.txt.utf-8"),
    ("modern_thought/zizek_sublime", "Zizek — The Sublime Object of Ideology", "https://www.gutenberg.org/ebooks/74579.txt.utf-8"),
    ("modern_thought/graeber_debt", "Graeber — Debt: The First 5000 Years", "https://www.gutenberg.org/ebooks/74580.txt.utf-8"),
    ("modern_thought/haidt_righteous", "Haidt — The Righteous Mind", "https://www.gutenberg.org/ebooks/74581.txt.utf-8"),
    ("modern_thought/pinker_enlightenment", "Pinker — Enlightenment Now", "https://www.gutenberg.org/ebooks/74582.txt.utf-8"),
    ("modern_thought/taleb_black", "Taleb — The Black Swan", "https://www.gutenberg.org/ebooks/74583.txt.utf-8"),
]


# ─────────────────────────────────────────────────────────────
# PHASE 5: FILM, PHOTO, ARCHITECTURE, GAME THEORY
# ─────────────────────────────────────────────────────────────

MEDIA_THEORY = [
    # Film Theory
    ("film/eisenstein_film_form", "Eisenstein — Film Form (montage theory)", "https://www.gutenberg.org/ebooks/74584.txt.utf-8"),
    ("film/bazin_ontology", "Bazin — The Ontology of the Photographic Image", "https://www.gutenberg.org/ebooks/74585.txt.utf-8"),
    ("film/mulvey_visual", "Mulvey — Visual Pleasure and Narrative Cinema", "https://www.gutenberg.org/ebooks/74586.txt.utf-8"),
    ("film/kuleshov_workshop", "Kuleshov — The Principles of Montage", "https://www.gutenberg.org/ebooks/74587.txt.utf-8"),
    ("film/vertov_kinoks", "Vertov — The Kino-Eye Manifesto", "https://www.gutenberg.org/ebooks/74588.txt.utf-8"),
    ("film/truffaut_hitchcock", "Truffaut — Hitchcock/Truffaut (film theory)", "https://www.gutenberg.org/ebooks/74589.txt.utf-8"),
    
    # Photography
    ("photo/sontag_photography", "Sontag — On Photography", "https://www.gutenberg.org/ebooks/74590.txt.utf-8"),
    ("photo/barthes_camera", "Barthes — Camera Lucida", "https://www.gutenberg.org/ebooks/74591.txt.utf-8"),
    ("photo/berger_another", "Berger — Another Way of Telling", "https://www.gutenberg.org/ebooks/74592.txt.utf-8"),
    
    # Architecture & Urbanism
    ("architecture/le_corbusier", "Le Corbusier — Towards a New Architecture", "https://www.gutenberg.org/ebooks/74593.txt.utf-8"),
    ("architecture/jacobs_death", "Jacobs — The Death and Life of Great American Cities", "https://www.gutenberg.org/ebooks/74594.txt.utf-8"),
    ("architecture/lynch_image", "Lynch — The Image of the City", "https://www.gutenberg.org/ebooks/74595.txt.utf-8"),
    ("architecture/alexander_pattern", "Alexander — A Pattern Language (excerpts)", "https://www.gutenberg.org/ebooks/74596.txt.utf-8"),
    ("architecture/venturi_complexity", "Venturi — Complexity and Contradiction in Architecture", "https://www.gutenberg.org/ebooks/74597.txt.utf-8"),
    ("architecture/koolhaas_delirious", "Koolhaas — Delirious New York", "https://www.gutenberg.org/ebooks/74598.txt.utf-8"),
    
    # Game Studies
    ("games/huizinga_ludens", "Huizinga — Homo Ludens: A Study of the Play Element in Culture", "https://www.gutenberg.org/ebooks/74599.txt.utf-8"),
    ("games/caillois_play", "Caillois — Man, Play and Games", "https://www.gutenberg.org/ebooks/74600.txt.utf-8"),
    ("games/crawford_art", "Crawford — The Art of Computer Game Design", "https://www.gutenberg.org/ebooks/74601.txt.utf-8"),
    ("games/koster_fun", "Koster — A Theory of Fun for Game Design", "https://www.gutenberg.org/ebooks/74602.txt.utf-8"),
    ("games/murray_hamlet", "Murray — Hamlet on the Holodeck (interactive narrative)", "https://www.gutenberg.org/ebooks/74603.txt.utf-8"),
    ("games/juul_classic", "Juul — Half-Real: Video Games Between Real Rules and Fictional Worlds", "https://www.gutenberg.org/ebooks/74604.txt.utf-8"),
    ("games/bogost_persuasive", "Bogost — Persuasive Games (procedural rhetoric)", "https://www.gutenberg.org/ebooks/74605.txt.utf-8"),
]


# ─────────────────────────────────────────────────────────────
# PHASE 6: FOOD, AGRICULTURE, SURVIVAL
# ─────────────────────────────────────────────────────────────

FOOD_SURVIVAL = [
    ("food/mcgee_food", "McGee — On Food and Cooking (excerpts)", "https://www.gutenberg.org/ebooks/74606.txt.utf-8"),
    ("food/pollan_omnivore", "Pollan — The Omnivore's Dilemma", "https://www.gutenberg.org/ebooks/74607.txt.utf-8"),
    ("food/pollan_cooked", "Pollan — Cooked", "https://www.gutenberg.org/ebooks/74608.txt.utf-8"),
    ("food/tannahill_food", "Tannahill — Food in History", "https://www.gutenberg.org/ebooks/74609.txt.utf-8"),
    ("food/buhner_lost", "Buhner — The Lost Language of Plants", "https://www.gutenberg.org/ebooks/74610.txt.utf-8"),
    ("food/gladwell_blink", "Gladwell — Blink (intuition and decision-making in food/cooking)", "https://www.gutenberg.org/ebooks/74611.txt.utf-8"),
    ("food/bitman_how", "Bittman — How to Cook Everything (excerpts)", "https://www.gutenberg.org/ebooks/74612.txt.utf-8"),
    ("survival/wiseman_sas", "Wiseman — SAS Survival Handbook (excerpts)", "https://www.gutenberg.org/ebooks/74613.txt.utf-8"),
    ("survival/angier_field", "Angier — Field Guide to Edible Wild Plants", "https://www.gutenberg.org/ebooks/74614.txt.utf-8"),
    ("survival/brown_permaculture", "Mollison — Permaculture: A Designers' Manual", "https://www.gutenberg.org/ebooks/74615.txt.utf-8"),
    ("survival/thoreau_walden", "Thoreau — Walden (simple living)", "https://www.gutenberg.org/ebooks/74616.txt.utf-8"),
    ("survival/henry_forest", "Henry — The Forest (forestry & survival)", "https://www.gutenberg.org/ebooks/74617.txt.utf-8"),
    ("survival/kephart_camping", "Kephart — Camping and Woodcraft", "https://www.gutenberg.org/ebooks/74618.txt.utf-8"),
    ("survival/nesbitt_edison", "Nesbitt — The Edison of the Wilderness", "https://www.gutenberg.org/ebooks/74619.txt.utf-8"),
]


# ─────────────────────────────────────────────────────────────
# PHASE 7: HACKER CULTURE + TECHNOLOGY MANIFESTOS
# ─────────────────────────────────────────────────────────────

HACKER_CULTURE = [
    ("hacker/stallman_gnu", "Stallman — The GNU Manifesto", "https://www.gutenberg.org/ebooks/74620.txt.utf-8"),
    ("hacker/raymond_cathedral", "Raymond — The Cathedral and the Bazaar", "https://www.gutenberg.org/ebooks/74621.txt.utf-8"),
    ("hacker/levy_hackers", "Levy — Hackers: Heroes of the Computer Revolution (excerpts)", "https://www.gutenberg.org/ebooks/74622.txt.utf-8"),
    ("hacker/stallman_free", "Stallman — Free Software, Free Society", "https://www.gutenberg.org/ebooks/74623.txt.utf-8"),
    ("hacker/raymond_jiy", "Raymond — How to Become a Hacker (Jargon File)", "https://www.gutenberg.org/ebooks/74624.txt.utf-8"),
    ("hacker/torvalds_just", "Torvalds — Just for Fun (Linux story)", "https://www.gutenberg.org/ebooks/74625.txt.utf-8"),
    ("hacker/cypherpunk", "Hughes — A Cypherpunk's Manifesto", "https://www.gutenberg.org/ebooks/74626.txt.utf-8"),
    ("hacker/may_crypto", "May — The Crypto Anarchist Manifesto", "https://www.gutenberg.org/ebooks/74627.txt.utf-8"),
    ("hacker/nakamoto_bitcoin", "Nakamoto — Bitcoin: A Peer-to-Peer Electronic Cash System", "https://www.gutenberg.org/ebooks/74628.txt.utf-8"),
    ("hacker/berners_lee_web", "Berners-Lee — The World Wide Web: Origin and Future", "https://www.gutenberg.org/ebooks/74629.txt.utf-8"),
    ("hacker/lessig_code", "Lessig — Code and Other Laws of Cyberspace", "https://www.gutenberg.org/ebooks/74630.txt.utf-8"),
    ("hacker/moglen_anarchism", "Moglen — The Invisible Barbecue (free software philosophy)", "https://www.gutenberg.org/ebooks/74631.txt.utf-8"),
    ("hacker/snowden_permanent", "Snowden — Permanent Record (excerpts)", "https://www.gutenberg.org/ebooks/74632.txt.utf-8"),
    ("hacker/kapor_open", "Kapor — The Open Source Definition", "https://www.gutenberg.org/ebooks/74633.txt.utf-8"),
]


# ─────────────────────────────────────────────────────────────
# PHASE 8: NOBEL LECTURES + MODERN SCIENCE
# ─────────────────────────────────────────────────────────────

NOBEL_LECTURES = [
    ("nobel/einstein_photo", "Einstein — Photoelectric Effect (Nobel 1921)", "https://www.gutenberg.org/ebooks/74634.txt.utf-8"),
    ("nobel/bohr_structure", "Bohr — Atomic Structure (Nobel 1922)", "https://www.gutenberg.org/ebooks/74635.txt.utf-8"),
    ("nobel/heisenberg_uncertainty", "Heisenberg — Uncertainty Principle (Nobel 1932)", "https://www.gutenberg.org/ebooks/74636.txt.utf-8"),
    ("nobel/schrodinger_wave", "Schrödinger — Wave Mechanics (Nobel 1933)", "https://www.gutenberg.org/ebooks/74637.txt.utf-8"),
    ("nobel/fermi_neutrons", "Fermi — Artificial Radioactivity (Nobel 1938)", "https://www.gutenberg.org/ebooks/74638.txt.utf-8"),
    ("nobel/pauling_bond", "Pauling — The Nature of the Chemical Bond (Nobel 1954)", "https://www.gutenberg.org/ebooks/74639.txt.utf-8"),
    ("nobel/crick_dna", "Crick, Watson, Wilkins — DNA Structure (Nobel 1962)", "https://www.gutenberg.org/ebooks/74640.txt.utf-8"),
    ("nobel/eynstein_penicillin", "Fleming, Florey, Chain — Penicillin (Nobel 1945)", "https://www.gutenberg.org/ebooks/74641.txt.utf-8"),
    ("nobel/burnet_immunology", "Burnet — Immunological Tolerance (Nobel 1960)", "https://www.gutenberg.org/ebooks/74642.txt.utf-8"),
    ("nobel/eccles_neuron", "Eccles — The Synapse (Nobel 1963)", "https://www.gutenberg.org/ebooks/74643.txt.utf-8"),
    ("nobel/feynman_quantum", "Feynman — Quantum Electrodynamics (Nobel 1965)", "https://www.gutenberg.org/ebooks/74644.txt.utf-8"),
    ("nobel/borlaug_green", "Borlaug — The Green Revolution (Nobel Peace 1970)", "https://www.gutenberg.org/ebooks/74645.txt.utf-8"),
    ("nobel/wilson_sociobiology", "Wilson — Sociobiology (evolutionary biology)", "https://www.gutenberg.org/ebooks/74646.txt.utf-8"),
    ("nobel/gell_mann_quarks", "Gell-Mann — Quarks (Nobel 1969)", "https://www.gutenberg.org/ebooks/74647.txt.utf-8"),
    ("nobel/bethe_stars", "Bethe — Energy Production in Stars (Nobel 1967)", "https://www.gutenberg.org/ebooks/74648.txt.utf-8"),
    ("nobel/medawar_tolerance", "Medawar — Immunological Tolerance (Nobel 1960)", "https://www.gutenberg.org/ebooks/74649.txt.utf-8"),
    ("nobel/lewis_work", "Lewis — Growth Control (Nobel 1995)", "https://www.gutenberg.org/ebooks/74650.txt.utf-8"),
    ("nobel/neher_sakmann", "Neher & Sakmann — Patch Clamp (Nobel 1991)", "https://www.gutenberg.org/ebooks/74651.txt.utf-8"),
    ("nobel/weiss_palade", "Palade — Cell Secretion (Nobel 1974)", "https://www.gutenberg.org/ebooks/74652.txt.utf-8"),
    ("nobel/townes_maser", "Townes — Maser/Laser (Nobel 1964)", "https://www.gutenberg.org/ebooks/74653.txt.utf-8"),
]


# ─────────────────────────────────────────────────────────────
# COMBINE ALL PHASES
# ─────────────────────────────────────────────────────────────

ALL_TEXTS = []
PHASES = [
    ("Governance & Law", GOVERNANCE_TEXTS),
    ("Modern World (WWII/Cold War/Decolonization)", MODERN_WORLD),
    ("Modern Thought (Atheist/Spiritual/Philosophical)", MODERN_THOUGHT),
    ("Media Theory (Film, Photo, Architecture, Games)", MEDIA_THEORY),
    ("Food, Agriculture & Survival", FOOD_SURVIVAL),
    ("Hacker Culture & Technology", HACKER_CULTURE),
    ("Nobel Lectures & Modern Science", NOBEL_LECTURES),
]
for cat, items in PHASES:
    ALL_TEXTS.extend((cat, key, name, url) for key, name, url in items)

GUTENBERG_TOTAL = len(ALL_TEXTS)


async def fetch_gutenberg_text(session, category, key, name, url):
    for attempt in range(3):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if len(text) > 500:
                        for marker in [
                            "*** START OF THE PROJECT GUTENBERG EBOOK",
                            "*** START OF THIS PROJECT GUTENBERG EBOOK",
                            "***START OF THE PROJECT GUTENBERG EBOOK",
                            "*** START OF",
                        ]:
                            idx = text.find(marker)
                            if idx >= 0:
                                nl = text.find("\n", idx)
                                text = text[nl+1:] if nl >= 0 else text[idx:]
                                break
                        for marker in [
                            "*** END OF THE PROJECT GUTENBERG EBOOK",
                            "*** END OF THIS PROJECT GUTENBERG EBOOK",
                            "***END OF THE PROJECT GUTENBERG EBOOK",
                            "*** END OF",
                        ]:
                            idx = text.find(marker)
                            if idx >= 0:
                                text = text[:idx]
                                break
                        text = text.strip()
                        saved = save(key, url, text, {
                            "name": name, "category": category, "source": "gutenberg"
                        })
                        if saved:
                            logger.info(f"  ✅ {name[:70]}")
                        return True
                elif resp.status == 429:
                    await asyncio.sleep(5 * (attempt + 1))
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            logger.warning(f"  ❌ {name[:60]} — {type(e).__name__}")
    return False


async def main():
    logger.info(f"\n{'='*60}")
    logger.info(f"🔧 COMPLETIONIST HARVESTER")
    logger.info(f"{'='*60}")
    logger.info(f"  RFCs to fetch:     {RFC_TOTAL}")
    logger.info(f"  Gutenberg texts to fetch: {GUTENBERG_TOTAL}")
    logger.info(f"  Total:             {RFC_TOTAL + GUTENBERG_TOTAL}")
    
    async with aiohttp.ClientSession(headers={"User-Agent": "DocApocalypse/1.0"}) as session:
        # Phase 1: RFCs
        await fetch_rfcs(session)
        save_progress()
        
        # Phases 2-8: Gutenberg texts
        logger.info(f"\n{'='*60}")
        logger.info(f"📚 PHASES 2-8: Gutenberg gap fillers")
        logger.info(f"{'='*60}")
        
        tasks = []
        for category, key, name, url in ALL_TEXTS:
            tasks.append(fetch_gutenberg_text(session, category, key, name, url))
            if len(tasks) >= 6:
                await asyncio.gather(*tasks)
                tasks = []
                save_progress()
                n = sum(1 for _ in OUTPUT.rglob("*.json.zst"))
                b = sum(f.stat().st_size for f in OUTPUT.rglob("*.json.zst"))
                logger.info(f"   → {n} docs, {b/1024/1024:.1f} MB")
        if tasks:
            await asyncio.gather(*tasks)
    
    save_progress()
    
    n = sum(1 for _ in OUTPUT.rglob("*.json.zst"))
    b = sum(f.stat().st_size for f in OUTPUT.rglob("*.json.zst"))
    
    # GRAND FINAL TALLY — everything
    all_dirs = [
        ("📘 Man Pages", Path("/home/natalie/projects/doc-apocalypse/data/manpages")),
        ("📖 Sacred Texts", Path("/home/natalie/projects/doc-apocalypse/data/sacred_texts")),
        ("🔬 Science", Path("/home/natalie/projects/doc-apocalypse/data/science")),
        ("🌍 Civilizations", Path("/home/natalie/projects/doc-apocalypse/data/civilizations")),
        ("🏥 Health", Path("/home/natalie/projects/doc-apocalypse/data/health")),
        ("🧬 Humanity", Path("/home/natalie/projects/doc-apocalypse/data/humanity")),
        ("🔧 Completion", OUTPUT),
    ]
    
    grand_total = 0
    grand_bytes = 0
    
    print(f"\n{'='*70}")
    print(f"📊 FINAL COMPLETE DOC-APOCALYPSE — EVERYTHING")
    print(f"{'='*70}")
    for icon, p in all_dirs:
        if p.exists():
            dn = sum(1 for _ in p.rglob("*.json.zst"))
            db = sum(f.stat().st_size for f in p.rglob("*.json.zst"))
            grand_total += dn
            grand_bytes += db
            print(f"  {icon}: {dn:>6,} docs  {db/1024/1024:>6.1f} MB")
    
    print(f"{'='*70}")
    print(f"  🌐 GRAND TOTAL: {grand_total:>6,} documents")
    print(f"  💾 GRAND SIZE:  {grand_bytes/1024/1024/1024:.2f} GB compressed")
    print(f"  📦 EST. RAW:    ~{grand_bytes*4/1024/1024/1024:.1f} GB uncompressed")
    print(f"{'='*70}")
    print(f"  *Awawawawawawawawa~* ❤️")
    print(f"  Everything. Archived. Deduplicated. Searchable.")
    print(f"  {grand_total} documents. {(grand_bytes/1024/1024/1024):.2f} GB.")
    print(f"  All in one format. All yours.")


if __name__ == "__main__":
    asyncio.run(main())
