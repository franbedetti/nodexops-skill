# NodeXOps Skill for Claude Code

A [Claude Code](https://claude.com/claude-code) skill that lets you bulk-edit product PDPs, content pages and blog posts in a [NodeXOps](https://nodexops.com)-managed Tiendanube store via API key.

Once installed, you can ask Claude things like:

> "Upload these 50 product descriptions from `products.csv` as drafts."
>
> "Regenerate the PDP for product 12345 with this new copy."
>
> "Create a block-group template called 'Cyber Monday' from product 999 and apply it to category 42."

## Install

```bash
# Clone into your Claude Code skills folder
mkdir -p ~/.claude/skills
git clone https://github.com/franbedetti/nodexops-skill.git ~/.claude/skills/nodexops
```

Restart Claude Code (or open a new session) so the skill is picked up.

## Setup (1-time)

1. Ask your NodeXOps admin for an **API key** scoped to your target store. The key looks like `nx_…` and is shown only once.
2. Save it in `~/.config/nodexops/.env`:

   ```bash
   NODEXOPS_BASE_URL=https://v2.nodexops.com
   NODEXOPS_API_KEY_MYSTORE=nx_xxxxxxxxxxxxxxxx
   NODEXOPS_STORE_ID_MYSTORE=12345
   ```

   Replace `MYSTORE` with a short name you use to refer to the store in conversation (e.g. `NODEXOPS_API_KEY_ACME` if your store is "Acme").

3. `pip install requests` — only dependency of the included Python client.

That's it. From any project, you can ask Claude to use the skill and it will load `client.py` plus the module/workflow docs as needed.

## What the skill can do

| Module           | Status       | What you can edit                                  |
|------------------|--------------|----------------------------------------------------|
| **NodexGen**     | ✅ Live      | Product PDPs (descriptions, draft/publish, blocks) |
| **Block Groups** | ✅ Live      | Reusable templates applied across many products    |
| **NodexPage**    | 🚧 Building  | Content pages (about, FAQ, landing)                |
| **NodexBlog**    | 🚧 Building  | Blog posts                                         |

It does **not** create products, change stock, prices, variants, or shipping — those stay in the Tiendanube admin or the TN API.

## How it works

When you ask Claude something content-related on the configured store, it loads:

- `SKILL.md` — table of contents + when to use / not use
- `client.py` — minimal Python wrapper (`requests`-only)
- The relevant `modules/*.md` (e.g. `nodexgen.md` for product descriptions)
- `workflows/*.md` recipes for common flows (bulk upload, draft-and-approve)
- `examples/*.py` runnable scripts you can adapt

## Updating

```bash
cd ~/.claude/skills/nodexops && git pull
```

## Source / contributions

This is a public mirror. The canonical source lives in the private NodeXOps platform repo and is auto-pushed here on every change. To report a bug or request a block type, open an issue on this repo — we'll triage upstream.

## License

MIT
