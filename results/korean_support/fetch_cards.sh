#!/usr/bin/env bash
# PART 1 raw evidence fetch. Run from the project root after `source env.sh`:
#   bash results/korean_support/fetch_cards.sh
# Everything lands under results/korean_support/cards/. Network required.
set -euo pipefail
C=results/korean_support/cards
mkdir -p "$C"

# Model cards (README.md at the Hub's current main) + full API metadata (tags, cardData.language, sha).
for r in convaiinnovations/laya-multilingual convaiinnovations/laya convaiinnovations/laya-typed-decisions jhu-clsp/mmBERT-base; do
  d="$C/$(echo "$r" | tr '/' '_')"
  mkdir -p "$d"
  .venv/bin/hf download "$r" README.md --local-dir "$d" >/dev/null
  curl -sf "https://huggingface.co/api/models/$r?full=true" -o "$d/api_model_full.json"
done

# File-level hashes: is the standalone laya-multilingual repo the same weights as the bundle
# subfolder pinned in models/ (convaiinnovations/laya@55cf4c4.../multilingual)?
curl -sf "https://huggingface.co/api/models/convaiinnovations/laya-multilingual?blobs=true" \
  -o "$C/convaiinnovations_laya-multilingual/api_model_blobs.json"
curl -sf "https://huggingface.co/api/models/convaiinnovations/laya/revision/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851?blobs=true" \
  -o "$C/convaiinnovations_laya/api_model_blobs_55cf4c4.json"

# mmBERT paper (arXiv 2509.06888): API record, abstract page, full HTML (Table 9 = per-language data).
P="$C/mmbert_paper"
mkdir -p "$P"
curl -sfL "https://export.arxiv.org/api/query?id_list=2509.06888" -o "$P/arxiv_api_2509.06888.xml"
curl -sfL "https://arxiv.org/abs/2509.06888" -o "$P/arxiv_abs_2509.06888.html"
curl -sfL "https://arxiv.org/html/2509.06888" -o "$P/arxiv_html_2509.06888.html"

# FineWeb2-HQ (the "20 high-resource languages" filtered set mmBERT uses after pre-training).
F="$C/epfml__FineWeb2-HQ"
mkdir -p "$F"
.venv/bin/hf download epfml/FineWeb2-HQ README.md --repo-type dataset --local-dir "$F" >/dev/null
curl -sf "https://huggingface.co/api/datasets/epfml/FineWeb2-HQ" -o "$F/api_dataset.json"

rm -rf "$C"/*/.cache
ls -la "$C"/*
