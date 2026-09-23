---
type: index
tags: [vault-organization]
---

## Projects

```dataview
TABLE status, created
FROM "projects"
WHERE type = "project"
SORT status ASC, file.mtime DESC
```

## Recent meetings

```dataview
LIST
FROM "projects"
WHERE type = "meeting"
SORT file.ctime DESC
LIMIT 10
```

## Inbox

```dataview
LIST
FROM "_inbox"
SORT file.ctime DESC
```
