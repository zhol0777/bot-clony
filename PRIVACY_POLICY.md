# Privacy Policy — bot-clony

**Last updated:** August 16, 2026

This privacy policy describes how the mechkeys Discord moderation bot ("bot-clony") collects, uses, stores, and handles your data when you interact with the mechkeys Discord server.

## 1. Data We Collect

### 1.1 User IDs (Discord Snowflakes)

We store Discord user IDs for the following purposes:

| Purpose | Retention | Storage |
|---|---|---|
| **Temporary eject tracking** (`UnejectTime`) | Until the eject expires | Raw ID, encrypted at rest |
| **Reminders** (`Reminder`) | Until the reminder fires | Raw ID, encrypted at rest |
| **Mechmarket search queries** (`MechmarketQuery`) | Until deleted by user | Raw ID, encrypted at rest |
| **Spam detection** (`MessageIdentifier`) | 5 minutes (auto-expired) | Raw ID, encrypted at rest |
| **Sticky role persistence** (`RoleAssignment`) | Until deleted by user or moderator | **One-way SHA-256 hash**, encrypted at rest |

### 1.2 Message Content

- **Hashed message content**: For spam detection, we compute a hash of your message content and compare it against recent messages from the same user. The hash is stored for **5 minutes** and then automatically deleted. The original message content is never stored.
- **Profanity scanning**: Message content is scanned in real-time against a banned wordlist. No plaintext content is stored from this scan.
- **Image hashing**: Image attachments are downloaded into memory, a perceptual hash is computed for duplicate detection, and the image is discarded. The hash is stored for **5 minutes**.
- **URL sanitization**: URLs in messages are read to strip tracking parameters. No data is stored from this process.

### 1.3 Human-Readable Content

- **Reminder text**: Text you provide when setting a reminder. Stored until the reminder fires.
- **Mechmarket search queries**: Text you provide when setting up a mechmarket alert. Stored until you delete it.
- **Wiki pages**: Community-curated page definitions (URLs and names). These are not personal data.

> Note: We previously stored moderator-issued warning reasons and social credit scores. These features have been **deprecated and removed**, and any associated previously stored data has been deleted as part of the privacy migration.

### 1.4 Sticky Role Tracking (Hashed IDs)

For sticky role persistence, we store a **one-way cryptographic hash** of your user ID (SHA-256 with a secret salt), not your actual user ID. This means:
- We can check if a joining user should have roles reapplied
- We **cannot** identify which user a hash belongs to from the database alone
- We **cannot** reverse the hash to recover your user ID

This design is intentional: it allows the moderation feature to function while minimizing the identifiability of stored data.

## 2. How We Use Your Data

- **Server moderation**: Anti-spam, anti-harassment, profanity filtering, role management, and user ejection tracking
- **Community features**: Wiki lookups, reminders, mechmarket price alerts
- **URL safety**: Stripping tracking parameters from shared URLs

We do **not** use your data for:
- Advertising or marketing
- Selling or sharing with third parties
- Training machine learning or AI models
- Profiling or discrimination

We no longer store warning reasons or social credit scores — those features have been discontinued to minimize data collection.

## 3. Data Encryption

All data stored by the bot is encrypted **at rest** using AES-256 via SQLCipher. The encryption key is stored as a server environment variable and is not accessible to anyone without server access.

## 4. Data Retention

| Data type | Retention period |
|---|---|
| Spam detection hashes (`MessageIdentifier`) | 5 minutes |
| Reminders (`Reminder`) | Until the reminder fires |
| Temporary ejects (`UnejectTime`) | Until the eject expires |
| Mechmarket queries, sticky roles | Until you or a moderator requests deletion |

## 5. Your Rights

### 5.1 Export Your Data

Use `!mydata export` to receive a DM with all data associated with your account.

### 5.2 Delete Your Data

Use `!mydata delete` to delete all data associated with your account. This removes:
- Reminders, eject records, mechmarket queries, and sticky role entries

(Note: warning reasons and social credit are no longer collected or stored.)

**Note**: Sticky role entries are keyed by a one-way hash of your user ID. When you run `!mydata delete`, the bot uses your current user ID to find and remove matching entries.

**What cannot be deleted**: Message identifiers (spam hashes) auto-expire within 5 minutes and are not stored long-term.

### 5.3 Opt Out of Tracking

Use `!mydata optout` to prevent the bot from:
- Tracking sticky roles (roles will not auto-reapply on rejoin)
- Tracking mechmarket search queries

**What opt-out does NOT prevent**: Server moderation actions (ejects, mutes) and spam detection — these protect the server and apply to all users equally.

Use `!mydata optin` to reverse the opt-out.

### 5.4 Privacy Policy

This policy is always available via the `!mydata privacy` command.

## 6. Third-Party Services

- **Reddit**: The mechmarket feature uses the Reddit API (`asyncpraw`) to fetch public Reddit posts. Reddit's privacy policy applies to data processed through their API.
- **Discord**: The bot operates through Discord's API. Discord's [Privacy Policy](https://discord.com/privacy) applies to data processed through their services.

## 7. Contact

For questions about this privacy policy or to request data deletion outside of the automated commands, contact the server moderators.

## 8. Changes to This Policy

We may update this privacy policy as needed. Changes will be announced in the server. Continued use of the bot after changes constitutes acceptance of the updated policy.
