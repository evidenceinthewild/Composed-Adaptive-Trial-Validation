# Release checks

These tools provide read-only checks for the public repository:

- retracted terminology and obsolete numerical results;
- agreement between rendered simulation figures and manuscript copies;
- presence of every figure in the manuscript PDF;
- consistency of manuscript source copies when additional copies are declared.

Run from the repository root after rendering the simulation and manuscript:

    python3 tools/release/test_release_tools.py
    python3 tools/release/check_release.py \
      --manifest tools/release/copies.example.toml \
      --workspace .

The checker never writes. Its exit status is 0 when all declared checks pass
and 1 when any blocker is found.

## Manifest

`copies.example.toml` is configured for this public checkout. Copy it only if
you need to add other manuscript formats or consumer directories:

    cp tools/release/copies.example.toml copies.toml

Machine-specific `copies.toml` files are ignored by Git.

Every manifest path is relative to the workspace supplied with
`--workspace`. A deck section is optional; the deck-image check is skipped when
no deck is declared.

## Porting additional manuscript formats

`port_manuscript.py` can transfer the canonical abstract and scientific body
into additional TeX wrappers declared in a manifest. It runs in check mode
unless `--apply` is supplied:

    python3 tools/release/port_manuscript.py \
      --manifest copies.toml --workspace .
    python3 tools/release/port_manuscript.py \
      --manifest copies.toml --workspace . --apply

All transformations validate their expected match counts before any file is
written.
