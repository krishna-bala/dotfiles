---
name: living-codebase-map
description: Create and maintain a living Excalidraw map of a codebase, or of one module in a monorepo; overlay planned changes before coding and sync the map after.
---

<!-- Source of truth: github.com/krishna-bala/dotfiles, modules/agents/skills/living-codebase-map. Edit there; other copies (claude.ai) are uploads of it. -->

# Living codebase map

One Excalidraw map per project, plus one per module in a monorepo. The map is the shared picture between the user and the agent: plans are reviewed on it, changes are synced to it. It is the user's thinking tool, built on Justin Sung's mind-mapping principles: chunked groups, labeled relationships, minimal text, directional flow, emphasis on what matters. The user rearranging boxes is part of how they learn, so never fight their edits.

Argument: an optional scope path (e.g. `packages/billing`). No argument means the whole repo.

## Files

- `docs/maps/INDEX.md`: one row per map with scope, map path, last-synced commit, one-line purpose.
- `docs/maps/overview.excalidraw`: the whole repo (or the only map, in a single-package repo).
- Monorepo modules: `<module>/docs/map.excalidraw`, so the map moves with the code. If INDEX.md records a different convention, follow that.

## Detecting a monorepo

Look for: `pnpm-workspace.yaml`, `workspaces` in package.json, `nx.json`, `turbo.json`, `lerna.json`, `[workspace]` in Cargo.toml, `go.work`, `WORKSPACE`/`MODULE.bazel`, `settings.gradle` with includes, uv/poetry workspaces. In a monorepo, the overview map's nodes are packages/apps and their dependency edges. Detail lives in module maps.

## Modes

Pick the mode from the request. If unclear: no map for the scope means Init; a pending task means Plan; otherwise Sync.

### Init (no map for this scope yet)
1. Optional recall step (skip if the user says "just build it"): ask the user to name the 3-7 main parts of this scope from memory, in one line. Afterwards, point out where the real map differs. That gap is the learning.
2. Explore the scope. For large scopes, delegate the sweep to a read-only search subagent if the harness has one, and keep only the conclusions: entry points, main components, data stores, external services, key flows.
3. Choose 5-12 nodes. More than 12 means chunk them into groups, or split detail into a sub-map.
4. Edges are relationships labeled with a verb: calls, reads, writes, publishes, imports, renders.
5. Lay out left to right in the direction of flow or dependency (entry points left, storage and external services right), on a grid of roughly 260px columns and 140px rows. Use frames or a background rectangle for groups.
6. Write the file, update INDEX.md with the current commit (`git rev-parse --short HEAD`), and validate (see below).
7. In a monorepo module: also add or update that module's node on the overview map with `link` set to the module map's path.

### Plan overlay (before implementing a change)
1. Read the map for the scope the change touches.
2. Add the proposed change as an overlay: new nodes and edges in orange (stroke `#f08c00`, fill `#fff4e6`), removals as red dashed (stroke `#e03131`, `strokeStyle: "dashed"`, opacity 60), modified nodes with an orange stroke at strokeWidth 4.
3. Tell the user in at most 5 lines what the overlay shows and what to check. No code yet. The user reviews the plan on the map.
4. Once approved, implement.

### Sync (after a change, or when the map is stale)
1. `git diff --stat <last-synced-commit>..HEAD -- <scope>` to see what moved.
2. Update only what changed: add, remove, or relabel agent-managed elements. Keep existing x/y positions. Clear any accepted overlay back to normal styling.
3. Update the commit in INDEX.md. Report in 1-3 lines what changed on the map.

### Zoom (module map in a monorepo)
Run Init for the module scope, then link it from the overview node.

## Rules

- Agent-managed element ids start with `map:` (`map:node:<slug>`, `map:edge:<from>-><to>`, plus `:label` for bound text). Any element without that prefix is the user's: never modify, move, or delete it.
- Never move an existing agent node. The user may have placed it deliberately. Place new nodes in free space near related ones.
- Labels are at most 4 words. No paragraphs on the map. If something needs explanation, add one small note text (fontSize 14) next to it, and only where it is non-obvious.
- Emphasis is reserved for what matters: the main flow gets strokeWidth 3, everything else 2.
- One map per scope. Don't create variants.
- Chat output stays short. The map is the explanation.

## Excalidraw format

A `.excalidraw` file is JSON: `{"type":"excalidraw","version":2,"source":"https://excalidraw.com","elements":[...],"appState":{"viewBackgroundColor":"#ffffff","gridSize":null},"files":{}}`. Use this helper to build elements; rectangles carry bound text, and arrows are bound to both ends and clipped to box edges.

```python
import json, random, time

def _base(id, type, x, y, w, h, **kw):
    e = dict(id=id, type=type, x=x, y=y, width=w, height=h, angle=0,
             strokeColor="#1e1e1e", backgroundColor="transparent", fillStyle="solid",
             strokeWidth=2, strokeStyle="solid", roughness=1, opacity=100,
             groupIds=[], frameId=None, roundness={"type": 3},
             seed=random.randint(1, 2**31), version=1,
             versionNonce=random.randint(1, 2**31), isDeleted=False,
             boundElements=[], updated=int(time.time() * 1000), link=None, locked=False)
    e.update(kw)
    return e

def _text(id, label, x, y, w, h, container, size=20):
    return _base(id, "text", x, y, w, h, roundness=None, text=label, originalText=label,
                 fontSize=size, fontFamily=5, textAlign="center", verticalAlign="middle",
                 containerId=container, lineHeight=1.25, autoResize=True)

def node(slug, label, x, y, w=180, h=70, fill="#e7f5ff", link=None, **kw):
    nid = f"map:node:{slug}"
    r = _base(nid, "rectangle", x, y, w, h, backgroundColor=fill, link=link, **kw)
    t = _text(f"{nid}:label", label, x + 10, y + h / 2 - 12, w - 20, 25, nid)
    r["boundElements"].append({"type": "text", "id": t["id"]})
    return [r, t]

def _clip(box, tx, ty, gap=8):
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (box["width"] / 2 + gap) / abs(dx) if dx else float("inf")
    sy = (box["height"] / 2 + gap) / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s

def edge(src, dst, label=None, **kw):
    """src/dst are rectangle dicts returned by node()[0]."""
    eid = f"map:edge:{src['id'][9:]}->{dst['id'][9:]}"
    scx, scy = src["x"] + src["width"] / 2, src["y"] + src["height"] / 2
    dcx, dcy = dst["x"] + dst["width"] / 2, dst["y"] + dst["height"] / 2
    x1, y1 = _clip(src, dcx, dcy)
    x2, y2 = _clip(dst, scx, scy)
    a = _base(eid, "arrow", x1, y1, abs(x2 - x1), abs(y2 - y1),
              roundness={"type": 2}, points=[[0, 0], [x2 - x1, y2 - y1]],
              lastCommittedPoint=None, startArrowhead=None, endArrowhead="arrow",
              startBinding={"elementId": src["id"], "focus": 0, "gap": 8},
              endBinding={"elementId": dst["id"], "focus": 0, "gap": 8}, **kw)
    src["boundElements"].append({"type": "arrow", "id": eid})
    dst["boundElements"].append({"type": "arrow", "id": eid})
    out = [a]
    if label:
        t = _text(f"{eid}:label", label, (x1 + x2) / 2 - 40, (y1 + y2) / 2 - 10, 80, 20, eid, size=16)
        a["boundElements"].append({"type": "text", "id": t["id"]})
        out.append(t)
    return out

def write_map(path, elements):
    doc = {"type": "excalidraw", "version": 2, "source": "https://excalidraw.com",
           "elements": elements,
           "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None},
           "files": {}}
    with open(path, "w") as f:
        json.dump(doc, f, indent=2)
```

When updating an existing map: load the JSON, keep every element whose id doesn't start with `map:` exactly as is, keep existing agent nodes' x/y, and rebuild agent edges from the current node positions (the user may have moved boxes).

## Validate before finishing

- The file parses as JSON, and all element ids are unique.
- Every `containerId`, `startBinding.elementId`, `endBinding.elementId` and `boundElements` id refers to an element that exists.
- No element without the `map:` prefix was changed (compare against the previous version).
- The node count is 12 or fewer per map.

Then tell the user to open the file in Excalidraw (the VS Code extension opens `.excalidraw` files directly) and to rearrange it freely.
