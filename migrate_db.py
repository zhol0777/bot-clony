'''
One-time migration script: migrate bot.db (plain SQLite) to encrypted.db (SQLCipher).
Hashes user_id values in RoleAssignment table during migration.

Usage:
    1. Set DATABASE_PASSPHRASE and HASH_SALT in your environment
    2. Run: uv run migrate_db.py
    3. Verify, then delete bot.db
'''
import hashlib
import os
import sys

HASH_SALT = os.getenv('HASH_SALT', '')
OLD_DB_PATH = 'bot.db'
NEW_DB_PATH = 'encrypted.db'

# Tables whose functionality was deprecated - their data is deliberately dropped,
# not carried into the encrypted database.
DROPPED_TABLES = ['warningmemberreason', 'socialcredit', 'stupidmessage']

if not os.getenv('DATABASE_PASSPHRASE'):
    print("ERROR: DATABASE_PASSPHRASE environment variable is not set.")
    sys.exit(1)
if not HASH_SALT:
    print("ERROR: HASH_SALT environment variable is not set.")
    sys.exit(1)

if os.path.exists(NEW_DB_PATH):
    print(f"ERROR: {NEW_DB_PATH} already exists. Remove it first to re-run migration.")
    sys.exit(1)

import peewee  # noqa: E402

import db  # noqa: E402

# Create tables in the encrypted database before migrating data
db.create_tables()


def hash_user_id(user_id: int) -> str:
    return hashlib.sha256(f"{user_id}{HASH_SALT}".encode()).hexdigest()


def table_names(peewee_db):
    cursor = peewee_db.execute_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'"
    )
    return [row[0] for row in cursor.fetchall()]


def main():  # noqa: PLR0914, PLR0915
    old_peewee = peewee.SqliteDatabase(OLD_DB_PATH)
    old_peewee.connect()
    old_tables = table_names(old_peewee)
    print(f"Found {len(old_tables)} table(s) in {OLD_DB_PATH}: {old_tables}")

    new_tables = table_names(db.bot_db)
    print(f"New schema has {len(new_tables)} table(s): {new_tables}")

    tables_to_migrate = [t for t in old_tables if t.lower() in [nt.lower() for nt in new_tables]]
    skip_tables = [t for t in old_tables if t not in tables_to_migrate]
    if skip_tables:
        print(f"Skipping tables not in new schema: {skip_tables}")

    # Deliberately drop deprecated tables and their tracked data.
    for table in DROPPED_TABLES:
        if table in old_tables:
            old_peewee.execute_sql(f'DROP TABLE IF EXISTS "{table}"')
            print(f"  Dropped deprecated table {table} from {OLD_DB_PATH}")
        else:
            print(f"  Deprecated table {table} not present, nothing to drop")

    total_rows = 0
    for table in tables_to_migrate:
        old_cursor = old_peewee.execute_sql(f'SELECT * FROM "{table}"')
        rows = old_cursor.fetchall()
        col_count = len(old_cursor.description)
        if not rows:
            print(f"  {table}: 0 rows (empty)")
            continue

        # Build INSERT with right number of placeholders
        placeholders = ', '.join(['?' for _ in range(col_count)])
        if table.lower() == 'roleassignment':
            # Old schema: user_id, role_name
            # New schema: hashed_user_id, role_name
            insert_sql = 'INSERT INTO "roleassignment" (hashed_user_id, role_name) VALUES (?, ?)'
            count = 0
            for row in rows:
                uid = row[1]  # user_id (row[0] is auto-increment id)
                role = row[2]  # role_name
                db.bot_db.execute_sql(insert_sql, [hash_user_id(uid), role])
                count += 1
            total_rows += count
            print(f"  {table}: {count} rows migrated (user_id hashed)")
        else:
            cols = ', '.join([f'"{d[0]}"' for d in old_cursor.description])
            insert_sql = f'INSERT OR IGNORE INTO "{table}" ({cols}) VALUES ({placeholders})'
            count = 0
            for row in rows:
                db.bot_db.execute_sql(insert_sql, list(row))
                count += 1
            total_rows += count
            print(f"  {table}: {count} rows migrated")

    print(f"\nTotal rows migrated: {total_rows}")

    print("\nVerification:")
    for table in sorted(tables_to_migrate):
        if table == 'sqlite_sequence':
            continue
        old_count = old_peewee.execute_sql(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        new_count = db.bot_db.execute_sql(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        match = "OK" if old_count == new_count else "MISMATCH"
        print(f"  {table}: old={old_count} new={new_count} [{match}]")

    old_peewee.close()
    db.bot_db.close()

    print(f"\nDone. Verify, then remove {OLD_DB_PATH}.")


if __name__ == '__main__':
    main()
