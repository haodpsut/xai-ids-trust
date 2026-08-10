#!/usr/bin/env python3
"""Layer-2 for a .bib that carries NO DOIs: find the record, then PROVE it is the right one.

The refs here were written from confident metadata, so there is nothing to look a DOI up by except
the title. That is exactly the operation L2-6 forbids as a *fallback* -- a title query that returns
whatever is closest and is then trusted. The rule it forbids is trusting an unverified match, not
querying by title. So this script queries by title and then refuses the result unless it can prove
identity independently:

  * the returned title must match the bib title after normalisation, AND
  * the first author surname must match, AND
  * the year must be within 1 (venue year vs publication year drift is ordinary).

Anything failing those is reported as NOT-MATCHED with the candidate shown, never silently accepted.
Entries a search cannot resolve (workshop papers, datasets, standards) are listed for manual
checking rather than counted as verified -- an unresolved reference is an unverified reference.

Output: l2-lookup.json (machine) + a table on stdout.
"""
import json
import re
import subprocess
import sys
import time
import unicodedata
import urllib.parse

sys.path.insert(0, "/Users/agentra/Documents/hao/working/paper-lab/my-skills/"
                   "workflow4paper/viet-paper-chuan-dph/scripts")
from verify_refs_layer2 import parse_bib, norm  # noqa: E402

UA = "User-Agent: paper-check/1.0 (mailto:noreply@example.org)"


def crossref_search(title, author, rows=5):
    q = urllib.parse.urlencode({"query.bibliographic": title[:300], "rows": rows,
                                "select": "title,author,issued,DOI,container-title,type"})
    url = "https://api.crossref.org/works?" + q
    try:
        r = subprocess.run(["curl", "-sL", "-H", UA, url],
                           capture_output=True, text=True, timeout=40)
        return json.loads(r.stdout)["message"]["items"]
    except Exception:
        return []


def surname(a):
    a = a.split(" and ")[0].strip()
    return a.split(",")[0].strip() if "," in a else a.split()[-1]


def main(bibpath):
    bib = parse_bib(open(bibpath, encoding="utf-8").read())
    print("L2 LOOKUP -- %d entries, none carry a DOI\n" % len(bib))
    out, ok, no, amb = {}, 0, 0, 0
    for key, (kind, f) in sorted(bib.items()):
        t, a, y = f.get("title", ""), f.get("author", ""), f.get("year", "")
        cands = crossref_search(t, a)
        time.sleep(0.35)
        hit = None
        for c in cands:
            ct = (c.get("title") or [""])[0]
            if norm(ct) != norm(t):
                continue
            cs = [x.get("family", "") for x in c.get("author", [])]
            if not cs or norm(cs[0]) != norm(surname(a)):
                continue
            cy = (c.get("issued", {}).get("date-parts") or [[None]])[0][0]
            if y and cy and abs(int(y) - int(cy)) > 1:
                continue
            hit = c
            break
        if hit:
            ok += 1
            out[key] = {"doi": hit["DOI"], "title": (hit.get("title") or [""])[0],
                        "year": (hit.get("issued", {}).get("date-parts") or [[None]])[0][0],
                        "venue": (hit.get("container-title") or [""])[0], "status": "MATCHED"}
            print("  %-22s MATCHED   %s" % (key, hit["DOI"]))
        else:
            near = (cands[0].get("title") or [""])[0][:60] if cands else "(no candidates)"
            if cands:
                amb += 1
                st = "NOT-MATCHED"
            else:
                no += 1
                st = "NO-RECORD"
            out[key] = {"status": st, "bib_title": t[:80], "closest": near}
            print("  %-22s %-11s closest: %s" % (key, st, near))
    json.dump(out, open("l2-lookup.json", "w"), indent=1)
    print("\n  MATCHED (identity proven): %d/%d" % (ok, len(bib)))
    print("  NOT-MATCHED (candidates exist but identity NOT proven): %d" % amb)
    print("  NO-RECORD (nothing returned): %d" % no)
    print("\n  Only MATCHED entries are verified. The rest must be opened by hand.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "refs.bib"))
