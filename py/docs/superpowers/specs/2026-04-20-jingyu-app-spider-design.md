# 鲸鱼APP Spider Design

## Overview
Port of the JS TVBox T4 plugin for 鲸鱼APP to Python, following existing spider patterns in the repo.

## Files
- `py/鲸鱼APP.py` — spider implementation
- `py/tests/test_鲸鱼APP.py` — unit tests

## Source Config
- **Host**: Dynamic, fetched from `https://jingyu4k-1312635929.cos.ap-nanjing.myqcloud.com/juyu3.json`
- **API Path**: `/api.php/qijiappapi.index` (api version 2)
- **AES**: CBC mode, key/iv = `AAdgrdghjfgsABC1`
- **Init endpoint**: `initV122`
- **UA**: `okhttp/3.10.0`

## Spider Methods

### `init(extend="")`
- Fetch host from COS URL, store as `self.host`
- Call `initV122` to populate categories and filters
- Store category config, area merge config, OCR config
- Check `system_search_verify_status` for search verification

### `homeContent(filter)`
- Return `class` list with blockedNames filtering, renameMap, forceOrder sorting
- Return `filters` dict per type_id with area merge and year auto-supplement applied

### `homeVideoContent()`
- Return `initData.type_list` flattened recommend_list

### `categoryContent(tid, pg, filter, extend)`
- POST to `typeFilterVodList` with type_id, page, area, year, sort, lang, class
- If area is merged value ("大陆"), query all merge values and deduplicate
- Return list + pagination metadata

### `detailContent(ids)`
- Try `vodDetail`, fallback `vodDetail2`
- Build play lines: filter blocked lines, rename displays, sort by order
- Encode each episode as `name$lineName@@mode@@parse_api,url,token+token,player_parse_type,parse_type`
- Return vod info with vod_play_from (line names $$$-separated) and vod_play_url (episodes #+$$$-separated)

### `searchContent(key, quick, pg="1")`
- POST to `searchList` with keywords, type_id=0, page
- If search verify enabled, fetch OCR code first
- Filter results by keyword match on name/remarks/class
- Exclude items with "屏蔽预留" in vod_class

### `playerContent(flag, id, vipFlags)`
- Parse id as `lineName@@mode@@payload`
- Handle modes:
  - `parse_type == '0'`: direct URL, parse=0
  - `parse_type == '2'`: prefix parse_api + url, parse=1
  - `player_parse_type == '2'`: GET parse_api+url, extract response.url, parse=0
  - default: AES encrypt url, POST to vodParse, extract inner.url, parse=0
- Return `{parse, jx, url, header}`

## Category Management
- `blockedNames`: ["全部"]
- `renameMap`: {} (identity)
- `forceOrder`: ["电影","电视剧","综艺","动漫","短剧"]

## Area Merge
- Merge ["中国大陆", "大陆", "内地"] → display as "大陆"
- When "大陆" selected in filter, query all merge values and deduplicate by vod_id

## Encryption
- AES-CBC with PKCS7 padding
- Key/IV: `AAdgrdghjfgsABC1` (UTF-8 encoded, 16 bytes)
- Encrypt: plaintext → AES encrypt → Base64
- Decrypt: Base64 → AES decrypt → plaintext → JSON parse
- Use `Crypto.Cipher.AES` from pycryptodome

## OCR Verification (optional)
- API: `http://154.222.22.188:9898/ocr/b64/text`
- Fetch captcha image, base64 encode, POST to OCR API
- Apply character replacement map for common misreads

## Dependencies
- `pycryptodome` (already in project via 瓜子.py)
- `requests` (base dependency)
- No new dependencies needed

## Test Strategy
- Mock `fetch`/`post` for network isolation
- Test AES encrypt/decrypt round-trip
- Test category processing (blocking, renaming, sorting)
- Test area merge logic
- Test playerContent parse modes with fixture payloads
- Test searchContent with mock response
