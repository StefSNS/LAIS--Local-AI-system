---
name: migrations
description: Database migration scripts and schema changes. Use when user asks about migrations, database changes, or schema updates.
---

# Migrations Skill

## When to Use

- User asks to "add migration", "create table"
- User asks about database schema changes
- User needs to rollback a change

## Migration Best Practices

### Create Migration

```python
# migrations/20260426_add_users.py

def up(db):
    db.create_table('users', {
        'id': 'SERIAL PRIMARY KEY',
        'email': 'VARCHAR(255) UNIQUE NOT NULL',
        'name': 'VARCHAR(100)',
        'created_at': 'TIMESTAMP DEFAULT NOW()'
    })

def down(db):
    db.drop_table('users')
```

### Run Migrations

```bash
alembic upgrade head
alembic downgrade -1
```

## Rules

1. **Always reversible**: Include `up()` and `down()`
2. **Never modify existing migrations**: Create new ones
3. **Small changes**: One change per migration
4. **Add indexes after data**: Separate migration
5. **Test locally first**

## Common Patterns

| Change | Approach |
|--------|----------|
| Add column | Add nullable, then backfill |
| Rename | Add new, copy, drop old |
| Remove column | Drop in separate migration |
| Create index | After data is populated |

## Safety Checklist

- [ ] Back up database before running
- [ ] Test on staging first
- [ ] Run during low traffic
- [ ] Have rollback plan
- [ ] Monitor after deployment