# Log file analysis for SEO: what Googlebot actually requested

log file analysis for seo starts from the lines the server wrote, not from a Search Console chart. Search Console summarises crawls you are allowed to see in that product. Combined access logs list the request: IP, time, method, path, status, bytes, referrer, user-agent. This repo keeps a sample of those lines and a stdlib Python parser that groups Googlebot-looking hits by status, path prefix, 404 clusters, and smartphone vs desktop UA.

The parser does not prove a request is genuine Googlebot. It matches the published user-agent tokens. Treat "Googlebot-looking" as a label on the UA string. For a browser-side pass over a log file, use the [Googlebot log file analyzer](https://indexfixtools.com/googlebot-log-analyzer). Data stays in the browser on that page. This README is the field notes for the columns that matter after the UA filter.

Google describes two Googlebot types in the [Googlebot documentation](https://developers.google.com/search/docs/crawling-indexing/googlebot): Googlebot Smartphone (mobile UA) and Googlebot Desktop. Both obey the same robots.txt product token. Most Search crawls of a typical site are the smartphone crawler. The subtype is in the HTTP user-agent header. This script splits on that string.

### What to extract first

| Slice | Why it matters | How this script prints it |
|---|---|---|
| Status codes | 200 vs 301/302 vs 404/410 vs 5xx is what the crawler received | counts by status |
| URL paths | Crawl budget spent on `/tag/`, `?sort=`, `/wp-json/` instead of canonical HTML | first path segment + query template |
| 404 clusters | Repeated 404s on one prefix are a template or a stale inbound link, not one typo | 404 rows grouped by path prefix |
| Smartphone vs desktop UA | Mobile-first indexing: the majority of Search crawls are smartphone | `smartphone` / `desktop` / `other-google` |

"Other-google" here means a UA that still contains a Google crawler token (for example `Googlebot-Image` or `Google-InspectionTool`) but is not the HTML Googlebot/2.1 pair. Those lines are counted, not mixed into the HTML Googlebot totals.

### Sample combined log

`sample-access.log` (Apache / Nginx combined format). Hostnames and IPs are fixtures.

Expected output from `python3 summarize_googlebot_log.py sample-access.log`:

```
# status
200	3
404	2
301	1

# ua
smartphone	5
desktop	1

# path
/blog	2
/tag	2
/wp-json	1
/old-page	1

# 404 prefix
/tag	2

# skipped_lines	0
```

Six Googlebot-looking HTML hits, one non-bot browser line ignored. Two 404s share `/tag`. The JSON endpoint is a 200: if that path should not be crawled, that is a robots/noindex problem, not a 404 problem. The sample is a fixture. It is not a client site.

### Run

```bash
python3 summarize_googlebot_log.py sample-access.log
```

Stdlib only (`re`). No keys. Lines that do not match combined format are skipped with a count at the end.

### FAQ

**Does a smartphone-heavy log mean desktop pages are unused?**
No. Googlebot documentation says most Search crawls use the smartphone crawler. Both types share the robots.txt token.

**Should every 404 be added to a sitemap?**
No. A 404 cluster is a crawl on a URL that should not exist or should redirect. Fix the template or the inbound link. Do not inventory dead paths.

**Is this the same as the Page indexing report?**
No. Logs show requests and statuses. The report shows how Google classified URLs it already knows about.
