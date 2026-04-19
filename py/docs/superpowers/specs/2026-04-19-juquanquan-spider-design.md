# 剧圈圈 Python 爬虫设计

## 目标

在当前 Python 仓库中新增一个符合 `base.spider.Spider` 接口的剧圈圈站点爬虫，覆盖以下能力：

- 首页分类与推荐
- 分类列表分页
- 联想搜索
- 详情信息与多线路播放列表
- 播放直链解析与接口回退

实现基于站点 HTML 和站内接口，不引入 JS 路由层，不修改 `base/` 公共层。

## 范围

本次实现包含：

- 新增独立脚本，文件名为 `剧圈圈.py`
- 新增独立单测，文件名为 `tests/test_剧圈圈.py`
- 固定主域为 `https://www.jqqzx.cc`
- 支持 `homeContent/homeVideoContent/categoryContent/detailContent/searchContent/playerContent`
- 首页固定分类为电影、剧集、动漫、综艺、短剧
- 详情解析基础信息与多线路播放列表
- 播放优先返回直链，无法直出时回退到站内解析接口

本次实现不包含：

- 筛选配置
- 多域名切换
- 浏览器自动化
- 站外驱动接入
- 账户登录或长期 cookie 持久化

## 方案选择

采用仓库现有的“单站点单文件 + 单测”方案。

对内拆分为：

- URL 与 id 互转
- 列表卡片解析
- 搜索结果解析
- 详情元信息解析
- 播放线路解析
- 播放页数据解码与回退

不直接照搬参考 JS 路由层的原因：

- 当前仓库消费的是 Python Spider 接口，不消费站内服务端路由
- 已有站点实现普遍使用 `self.fetch + lxml/xpath/regex`，应延续既有结构
- 本次重点是站点能力迁移，不是路由层复刻

## ID 设计

用户要求“都尽量压缩成站内 id”，因此统一采用短路径形式，而不是完整 URL。

### 详情 id

列表与搜索返回：

- `vod/<数字id>`

例如：

- `vod/12345`

内部在 `detailContent` 中还原为：

- `https://www.jqqzx.cc/vod/12345.html`

### 播放 id

详情播放列表返回：

- `play/<数字id-线路序号-剧集序号>`

例如：

- `play/12345-1-1`

内部在 `playerContent` 中还原为：

- `https://www.jqqzx.cc/play/12345-1-1.html`

这样可以：

- 避免在返回数据中暴露完整 URL
- 保持 id 可读
- 与站内 URL 结构一一对应
- 降低与其他站点数字 id 混淆的概率

## 模块边界

新增脚本只在站点文件内部维护逻辑，不修改 `base/`。

脚本职责拆分如下：

- `init`
  - 初始化主域、请求头和固定分类
- `homeContent`
  - 返回固定分类
- `homeVideoContent`
  - 抓首页并解析推荐卡片
- `categoryContent`
  - 构造分类分页 URL，请求 HTML 并解析卡片
- `detailContent`
  - 还原详情 URL，解析元信息与多线路播放列表
- `searchContent`
  - 请求联想搜索接口并映射为卡片列表
- `playerContent`
  - 还原播放 URL，优先返回直链，失败时回退站内解析接口
- 私有 helper
  - 文本清洗
  - 绝对 URL 组装
  - 详情 id 与播放 id 编解码
  - cookie 合并
  - 播放页数据提取与解码

## Host 与请求策略

本次只实现单域：

- `https://www.jqqzx.cc`

请求统一通过 `self.fetch` 发起，固定请求头至少包含：

- `User-Agent`
- `Accept-Language`
- `Referer`

请求原则：

- HTML / JSON 请求超时固定为 10 秒
- 请求失败时返回空结果或兜底播放结果，不抛出未处理异常
- 仅在 `playerContent` 内维护本次请求链路所需的临时 cookie

## 首页与分类设计

首页分类固定为：

- `dianying -> 电影`
- `juji -> 剧集`
- `dongman -> 动漫`
- `zongyi -> 综艺`
- `duanju -> 短剧`

`homeContent` 返回：

- `class`

不返回筛选配置。

`homeVideoContent`：

- 请求首页
- 解析推荐卡片
- 最多返回前 40 条

分类 URL 规则：

- `/type/<分类id>/page/<页码>.html`

分类返回字段：

- `page`
- `pagecount`
- `total`
- `list`

分页策略采用保守估计：

- 当前页有数据时，`pagecount = page + 1`
- 当前页无数据时，`pagecount = page`

## 列表与搜索设计

分类页和首页卡片解析规则：

- 外层：`a.module-poster-item.module-item`
- 标题：`.module-poster-item-title` 或 `title/alt`
- 封面：`img` 的 `data-original` 或 `src`
- 备注：`.module-item-note`

输出统一卡片结构：

- `vod_id`
- `vod_name`
- `vod_pic`
- `vod_remarks`

搜索使用联想接口：

- `/index.php/ajax/suggest?mid=1&wd=<关键词>`

返回 JSON 后映射为卡片列表。搜索结果中的详情 id 也压缩为：

- `vod/<数字id>`

搜索无分页，固定返回：

- `page = 当前请求页`
- `pagecount = 1`

## 详情页设计

详情页解析以下字段：

- 标题
- 封面
- 类型
- 备注或状态
- 主演
- 导演
- 剧情简介
- 多线路播放列表

输出至少包含：

- `vod_id`
- `vod_name`
- `vod_pic`
- `type_name`
- `vod_remarks`
- `vod_actor`
- `vod_director`
- `vod_content`
- `vod_play_from`
- `vod_play_url`

线路解析规则：

- 线路名来自 `#y-playList .module-tab-item`
- 每个线路对应一个 `.his-tab-list`
- 剧集项来自 `a.module-play-list-link[href]`
- 剧集名优先取 `span` 文本，回退到节点文本
- 剧集链接压缩成 `play/<id>`

播放列表输出形如：

- `vod_play_from = 线路1$$$线路2`
- `vod_play_url = 第1集$play/123-1-1#第2集$play/123-1-2$$$正片$play/123-2-1`

## 播放设计

`playerContent(flag, id, vipFlags)` 处理流程：

1. 将 `play/<id>` 还原为播放页 URL
2. 请求播放页并提取 `player_aaaa`
3. 优先尝试从 `player_aaaa.url` 解出真实地址
4. 若解出的是直链媒体地址，则直接返回
5. 若不是直链，则请求：
   - `/jx/player.php?vid=<vid>`
   - `/jx/api.php`
6. 若接口成功返回可解出的真实地址，则返回直链
7. 若仍失败，则回退为播放页地址并设置 `parse=1`

### 播放解码

保留参考实现中的三段能力：

- Base64 解码
- `md5("test")` 派生 key 的 XOR 解码
- `error://apiRes_` 前缀清洗与字母映射恢复

直链判定标准：

- `http/https`
- 末尾或查询参数前匹配 `m3u8/mp4/flv/m4s`

### 播放返回策略

直链成功时返回：

- `parse = 0`
- `jx = 0`
- `url = 真实播放地址`

无法直出时返回：

- `parse = 1`
- `jx = 1`
- `url = 还原后的播放页地址` 或中间地址

## 错误处理

- HTML 解析失败时返回空列表或空字符串，不抛出未处理异常
- 搜索 JSON 解析失败时返回空搜索结果
- `player_aaaa` 缺失时，`playerContent` 回退为解析播放页
- 解析接口返回非法 JSON 时，记录日志并回退
- cookie 仅在当前 `playerContent` 调用内合并，不做跨请求缓存

## 测试设计

新增 `tests/test_剧圈圈.py`，至少覆盖：

- 首页分类返回固定五类
- 首页推荐卡片解析
- 分类 URL 构造与分页返回
- 搜索 JSON 映射为压缩后的 `vod/<id>`
- 详情页元信息提取
- 多线路播放列表解析为压缩后的 `play/<id>`
- 直链播放返回
- 解析接口回退成功
- `player_aaaa` 缺失时回退到播放页

测试全部使用 mock HTML / JSON，不依赖外网。

## 验收标准

- 新增 `剧圈圈.py`
- 新增 `tests/test_剧圈圈.py`
- `home/category/detail/search/player` 都能返回符合当前仓库习惯的数据结构
- `vod_id` 与播放 id 均压缩为站内短 id，不暴露完整 URL
- 播放逻辑满足“直链优先，解析接口回退”
- 新增测试可独立通过
