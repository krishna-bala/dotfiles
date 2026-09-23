---
type: index
tags: [vault-organization]
---

## Projects

```dataview
TABLE status, created
WHERE type = "project" AND status != "complete"
SORT status ASC, file.mtime DESC
```

## Inbox

New notes land in `_inbox/`. Move each one to its folder once it has a home.

```dataview
LIST
FROM "_inbox"
SORT file.ctime DESC
```

## Recently edited

```dataview
LIST
WHERE file.name != this.file.name
SORT file.mtime DESC
LIMIT 10
```
