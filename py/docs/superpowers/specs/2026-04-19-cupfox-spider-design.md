# 茶杯狐 Python 爬虫设计

## 目标

在当前 Python 仓库中新增一个符合 `base.spider.Spider` 接口的茶杯狐站点爬虫，完整覆盖以下能力：

- 首页分类
- 首页推荐
- 分类列表
- 搜索
- 详情解析
- 播放解析
- 搜索/详情/播放页面的人机验证绕过

实现基于站点 HTML 页面和 `foxplay` 接口，不引入服务端路由层，不修改 `base/` 公共层，并保持当前仓库的短 ID 和结果结构约定。

## 范围

本次实现包含：

- 新增独立脚本，文件名为 `茶杯狐.py`
- 新增对应单元测试 `tests/test_茶杯狐.py`
- 使用单一站点主域：`https://www.cupfox.ai`
- 支持 `home/homeVideo/category/search/detail/player` 主链路
- 实现命中验证页后的 Cookie 合并、`token` 提取和 `/robot.php` 过盾请求
- 实现 `foxplay/api.php` 的两种播放链接解密
- 过滤 404 占位、403 和明显不可用链接，并在失败时回退 `parse=1`

本次实现不包含：

- 多域名探活与自动切换
- 浏览器自动化、JS 引擎执行和验证码识别
- 站外搜索源聚合和非站内播放链路修复
- 登录态管理和本地缓存持久化

## 方案选择

采用仓库现有的“单站点单文件 + 单测”方案：

- 对外保持 `Spider` 接口兼容
- 对内拆分为短 ID 处理、请求与过盾、卡片解析、详情解析、播放解密几个 helper
- 只在站点文件内部维护逻辑，不修改 `base/`

不直接照搬参考 JS 路由层的原因是：

- 当前仓库只消费 Spider 接口，不消费 Node 路由插件
- Python 版已有稳定的 HTML 爬虫实现风格，应延续既有结构
- 本次重点是把茶杯狐能力转成可测试的 Python Spider，而不是保留一层额外运行时

## 模块边界

新增脚本内部职责拆分如下：

- `init`
  - 初始化主域、请求头、分页大小和字符映射表
- `homeContent`
  - 返回分类列表和静态筛选空结构
- `homeVideoContent`
  - 请求首页并解析推荐卡片，去重后截断
- `categoryContent`
  - 请求分类页，复用卡片解析并返回页码、总量估算和列表
- `searchContent`
  - 请求搜索页，复用卡片解析并支持 `quick`
- `detailContent`
  - 请求详情页，提取元数据和多线路播放列表
- `playerContent`
  - 请求播放页、提取 `player_aaaa`、调用 `foxplay/api.php`、解密直链并决定是否回退解析
- 私有辅助函数
  - URL 补全与短 ID 编解码
  - HTML 请求与过盾流程
  - Cookie 合并
  - `token` 提取和过盾加密
  - `player_aaaa` 解析
  - 两套播放解密
  - 占位/禁播链接识别

## ID 与 URL 设计

遵循当前仓库“短 ID，不暴露完整 URL”的约定。

详情页短 ID：

- 页面链接 `/movie/<slug>.html`
- 存储为 `detail/<slug>`

播放页短 ID：

- 页面链接 `/play/<slug>.html`
- 存储为 `play/<slug>`

编码与解码原则：

- 只接受站内标准详情/播放路径
- 解析失败时返回空字符串，调用侧直接回空结果或回退
- 内部统一通过 `urljoin` 补全相对路径

## Host 与请求策略

本次只实现单域：

- `https://www.cupfox.ai`

统一请求头至少包含：

- `User-Agent`
- `Referer`
- `Accept`
- `Accept-Language`

请求原则：

- HTML 请求超时固定为 15 秒
- 普通页面请求走 `self.fetch` / `self.post`
- 页面请求默认不自动依赖持久会话，而是在单次过盾流程里显式维护 Cookie 字典
- 命中验证时只处理当前请求，不做全局 Cookie 缓存
- 请求失败时返回空结果或播放页回退，不抛出未处理异常

## 过盾设计

页面请求统一走 `_request_with_firewall()`：

1. 首次请求目标 URL，收集响应文本和 `set-cookie`
2. 如果页面不包含 `人机验证` 或 `verifyBox`，直接返回 HTML
3. 如果命中验证，从 HTML 中提取 `var token = encrypt("...")`
4. 对当前 URL 和原始 token 分别执行参考实现中的字符位移 + 随机填充 + Base64 加密
5. 向 `/robot.php` 发起表单 POST，请求头带上已收集 Cookie
6. 合并验证接口返回的 Cookie
7. 带最新 Cookie 二次请求原页面
8. 若二次请求仍是验证页，则按失败处理

该流程只用于 HTML 页面：

- 首页
- 分类页
- 搜索页
- 详情页
- 播放页

`foxplay/api.php` 不走过盾流程。

## 分类、首页与搜索设计

### 分类

分类从首页导航 `nav.bm-item-list a` 动态解析，提取：

- `type_id`
- `type_name`

只保留 `/type/<id>.html` 结构的导航链接。

### 首页推荐

首页推荐从 `.mobile-main .panel .movie-list-item` 提取，按详情 URL 去重后返回前 20 条。

### 分类列表

分类页路径：

- `/type/<type>-<page>.html`

每张卡片提取：

- 链接：`a[href]`
- 标题：`a[title]`
- 封面：`.Lazy[data-original]`
- 备注：`.movie-item-note`，为空时退回 `.movie-item-score`

### 搜索

搜索页路径：

- `/search/<keyword>----------<page>---.html`

搜索结果按 `.vod-search-list .box` 解析，字段提取规则与分类卡片一致，但标题优先取 `.movie-title`。

返回策略：

- `limit` 固定为 20
- 列表和搜索返回 `page`、`total`、`limit`、`list`
- 不返回 `pagecount`
- 当页结果为空时 `total` 为 0
- 当页结果非空时，`total` 至少保证大于等于 `page * len(list)`，避免上层立即判定无后续分页

## 详情页设计

详情页解析以下字段：

- `vod_id`
- `vod_name`
- `vod_pic`
- `vod_content`
- `vod_year`
- `vod_director`
- `vod_actor`
- `vod_play_from`
- `vod_play_url`

解析策略：

- 标题取 `h1.movie-title`
- 海报取 `.poster img`
- 简介取 `.summary.detailsTxt` 的纯文本，并移除展开按钮文本
- 年份从 `.scroll-content a` 中提取四位数字
- 导演和演员从 `.info-data` 中按标签文案识别并拼接

播放列表策略：

- 线路名从 `.play_source_tab .swiper-slide` 提取
- 每个 `.play_list_box` 对应一组线路
- 集数条目从 `.content_playlist li a` 提取为 `名称$play/<slug>`
- 最终按仓库约定拼接成 `vod_play_from` 和 `vod_play_url`

如果线路数和列表数不一致：

- 优先保留已有剧集列表
- 缺失的线路名回退为 `线路<n>`

## 播放解析设计

### 播放页提取

`playerContent` 先还原播放页 URL，请求 HTML，再从脚本中提取：

- `player_aaaa.url`
- `player_aaaa.from`
- `player_aaaa.server`

如果找不到 `player_aaaa.url`，直接回退：

- `parse = 1`
- `url = 播放页 URL`
- `header` 带 `User-Agent` 和当前页 `Referer`

### `foxplay/api.php`

当 `player_aaaa.url` 存在时：

1. 以 `vid=<player_aaaa.url>` POST 到 `/foxplay/api.php`
2. 若接口返回 `data.url`，按 `urlmode` 解密：
   - `1` 走 `Decode1.sign`
   - `2` 走 `decode2`
   - 其他值直接使用原始 `url`
3. 对解密结果做占位链接识别

### 解密规则

`Decode1.sign` 对应参考实现的三段式处理：

- 自定义异或解码
- Base64 还原映射表
- 按明文/密文字母映射恢复真实路径

`decode2` 对应参考实现的字典反向位移逻辑：

- Base64 解码
- 每三个字符取中间位
- 按字典回退 3 位

### 占位链接识别

以下情况视为不可用直链：

- 空字符串
- 非 `http(s)` / `//` / `magnet:` 链接
- 指向 `404.mp4`
- 参数含 `code=403`
- 包含 `forbidden`

### 播放返回策略

如果解密得到可用直链：

- 返回 `parse = 0`
- `url` 为真实地址
- `header.Referer` 指向 `muiplayer.php?vid=...`

如果 API 无直链、解密失败或命中占位链接：

- 返回 `parse = 1`
- `url` 为原播放页
- `header.Referer` 指向原播放页

## 错误处理

所有对外方法在站点异常时返回兼容结构，不抛出未处理异常：

- `homeContent` 返回空分类
- `homeVideoContent` 返回空列表
- `categoryContent` 返回当前页和空列表
- `searchContent` 返回当前页和空列表
- `detailContent` 返回空 `list`
- `playerContent` 返回原播放页的 `parse=1`

内部异常处理原则：

- 私有 helper 可抛出 `ValueError`
- 对外接口统一兜底
- JSON 解析、Base64 解码和映射解密失败时返回空字符串，不中断整个请求

## 测试设计

测试采用 `unittest` 和 `unittest.mock`，避免真实网络访问。

首批覆盖：

- 短 ID 编解码
- Cookie 合并和请求头拼装
- 验证页 `token` 提取和过盾二次请求
- 首页分类解析
- 首页推荐去重
- 分类列表解析
- 搜索结果解析和空关键词分支
- 详情页元数据和多线路播放列表拼装
- `Decode1` 与 `decode2` 的解密行为
- `playerContent` 的直链成功分支
- `playerContent` 的占位链接回退分支
- `playerContent` 的缺失 `player_aaaa` 回退分支

测试粒度要求：

- 先验证最小私有 helper
- 再验证对外接口方法
- 只 mock 网络层，不 mock 纯解析函数

## 验收标准

满足以下条件视为完成：

- 新增 `茶杯狐.py`，接口与仓库现有 Spider 一致
- 新增 `tests/test_茶杯狐.py`
- 列表和搜索结果使用短详情 ID
- 详情页播放列表使用短播放 ID
- 命中验证页时能完成两次请求和 Cookie 合并
- `playerContent` 能在可用时返回直链，在不可用时稳定回退
- 相关测试通过，且不引入 `pagecount` 到列表/搜索返回结构
