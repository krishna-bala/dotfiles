---
name: tiling-tree
user-invocable: true
disable-model-invocation: false
description: >
  Interactive tiling tree method for systematically mapping solution spaces.
  Decomposes a problem into MECE (mutually exclusive, collectively exhaustive)
  branches with low branching factor. Use when exploring solution spaces,
  brainstorming approaches, evaluating architectural alternatives, or needing
  comprehensive coverage of options. Also known as morphological analysis
  (Fritz Zwicky). Triggers on: "tiling tree", "solution space", "map out approaches",
  "morphological analysis", "MECE", "all possible ways to", "systematic brainstorm",
  "explore alternatives"
argument-hint: "[problem or solution space to explore]"
---

# Tiling Tree: $ARGUMENTS

Systematically map the solution space by constructing a tiling tree, a recursive MECE decomposition that forces comprehensive exploration of all possible approaches.

A tiling tree takes the complete set of possible solutions to a problem and splits it into non-overlapping subsets that together cover the entire original set. Each subset is split further, recursively, until reaching concrete actionable ideas. The method's value comes from forcing you to think about branches you'd normally skip.

## Interaction approach

Work through the tree interactively with the user, one level at a time. Do not generate the whole tree unprompted. The user's thinking at each split is the point, not the final artifact.

### Phase 1: Define the root

Ask the user to precisely define the solution space:

- "What problem are you trying to solve? State it as specifically as you can."
- "What constraints bound the solution space? What's definitely out of scope?"
- "What does a successful solution look like?"

Push for precise language. The root definition determines everything downstream. If the user says "improve performance," ask: whose performance? measured how? under what conditions?

Write out the agreed root definition explicitly before proceeding.

### Phase 2: Find the first split

Guide the user to the most natural top-level decomposition:

- "What's the most fundamental dimension along which solutions to this problem differ?"
- "If you had to sort every possible approach into a few buckets, what would those buckets be?"

**Branching factor guidance:**
- Aim for 3-5 branches per node. This maps well to how humans naturally categorize and reason about trade-offs.
- Binary splits ("has X" / "doesn't have X") are allowed when genuinely natural, but don't default to them. They often create an artificial "everything else" bucket that hides interesting structure.
- More than 5 branches usually means two split dimensions are mixed together. Split one dimension first, then the other at the next level down.

**What makes a good split:**
- It exposes a meaningful trade-off (cost vs. capability, simplicity vs. flexibility, etc.)
- The branches are grounded in something durable: physical principles, mathematical properties, or fundamental mechanisms
- Each branch suggests a genuinely different class of approach, not just a parameter variation

**MECE check (do this at every split):**
- Mutually exclusive: "Could a solution plausibly belong to two of these branches?" If yes, rework the split.
- Collectively exhaustive: "Can you think of a valid approach that doesn't fit any branch?" If yes, a branch is missing.

### Phase 3: Recursive decomposition

For each branch at the current level:

1. Define it precisely: what's included, what's excluded
2. Ask: "Can this branch be split further into a few natural sub-categories?"
3. Apply the same MECE checks and split quality criteria
4. Stop splitting when you reach:
   - Concrete, actionable approaches (leaf nodes)
   - Branches that are clearly infeasible (mark why)
   - Branches that need investigation before splitting further

**Work breadth-first**, completing one full level before going deeper. This prevents tunnel vision on a single branch and helps spot cross-branch patterns.

**Force exploration on every branch**, especially ones the user wants to dismiss quickly. Ask: "Before we mark this as infeasible, what would have to be true for this approach to work?" Dead-end branches with documented reasoning are valuable. They prevent revisiting the same dead end later, and may become viable when circumstances change.

### Phase 4: Evaluate leaves

For each leaf node, assign a status:

- `[promising]` — Worth pursuing. Note key advantages and risks.
- `[dead end]` — Infeasible or clearly dominated. Note the specific reason so it can be revisited if conditions change.
- `[needs research]` — Can't evaluate without more information. Note what specifically needs investigation.
- `[exists]` — Already implemented or well-known. Note the reference.

### Phase 5: Reflect

After completing the tree:

- "Which branches surprised you? What approaches hadn't you considered?"
- "Are there alternative ways to split at the top level that might reveal different solutions?"
- "Which 'needs research' branches have the highest potential upside?"

Different top-level split dimensions provoke genuinely different ideas. Offer to construct a second tree from a different angle if the user wants to explore further.

## Output format

Present the completed tree as structured text with clear hierarchy:

```
Root: [precise problem definition]

Split by: [dimension name]
├── Branch A: [precise definition]
│   Split by: [sub-dimension]
│   ├── A.1: [description] [promising] — key advantage
│   ├── A.2: [description] [dead end] — reason
│   └── A.3: [description] [needs research] — what to investigate
├── Branch B: [precise definition]
│   ├── B.1: [description] [promising] — key advantage
│   └── B.2: [description] [exists] — reference
└── Branch C: [precise definition]
    └── (needs further decomposition)
```

Label each split dimension explicitly. This makes it easy to see when dimensions have been mixed at the same level.

## Facilitation principles

- **One level at a time**: The user's reasoning at each split matters more than the finished tree.
- **Precision over speed**: Spend time getting definitions right. Sloppy labels cause MECE violations and hide gaps.
- **Challenge completeness relentlessly**: "What's missing?" is the most valuable question in this method. Novel ideas emerge from gaps you're forced to fill.
- **Dead ends are documentation**: A branch marked infeasible with a clear reason is valuable work, not wasted effort.
- **Trees are snapshots, not verdicts**: Branches dismissed today may become viable as technology, costs, or knowledge change. Note assumptions that could shift.
