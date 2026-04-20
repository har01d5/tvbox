# 乐兔 Python 爬虫设计

## 目标

在当前 Python 仓库中新增一个符合 `base.spider.Spider` 接口的乐兔站点爬虫，覆盖以下能力：

- 首页分类
- 分类列表
- 搜索
- 详情解析
- 播放解析

实现以用户提供的 Node/JS 版本为行为参考，但落地形式遵循当前仓库的单文件 Spider 约定。

## 范围

本次实现包含：

- 新增独立脚本，文件名为 `乐兔.py`
- 使用单一站点主域：`https://www.letu.me`
- 支持 `home/category/detail/search/player` 全链路
- 返回仓库当前通用的视频字段
- 对详情和播放地址使用站内短 ID
- 为新增行为补齐 `unittest`

本次实现不包含：

- Node/Fastify 路由层
- 站点扩展筛选
- 多域名探活和切换
- 浏览器执行、验证码处理或动态反爬绕过
- 修改 `base/` 公共层

## 方案选择

采用仓库现有的“单站点单文件 + 单测”方案：

- 对外保持 `Spider` 接口兼容
- 对内拆分成 URL 组装、短 ID 编解码、列表解析、详情解析、播放解析几个 helper
- 保留参考 JS 的主要分支，但去掉与仓库无关的 HTTP 路由包装

不直接照搬参考 JS 路由层的原因是：

- 当前仓库消费的是 Spider 方法，不是站内 HTTP API
- 单文件 Spider 与现有项目结构一致，测试也更直接
- Python 版重点应落在字段映射与解析行为，而不是请求分发

## 模块边界

新增脚本只在站点文件内部维护逻辑，不修改 `base/`。

脚本内部职责拆分如下：

- `init`
  - 初始化主域、请求头、分类定义
- `homeContent`
  - 返回固定分类，不内联推荐列表
- `homeVideoContent`
  - 返回空列表，保持与多数现有 Spider 一致
- `categoryContent`
  - 请求分类页并返回分页结果
- `detailContent`
  - 请求详情页并整理影片元数据与播放列表
- `searchContent`
  - 请求搜索页并映射结果列表
- `playerContent`
  - 解析播放页，优先输出直链，失败时回退系统解析
- 私有辅助函数
  - URL 组装
  - 文本清洗
  - 详情与播放短 ID 编解码
  - 列表卡片解析
  - 详情信息提取
  - 播放配置解析

## Host 与请求策略

本次只实现单域：

- `https://www.letu.me`

请求策略：

- 默认使用站点页面 HTML，不依赖隐藏接口
- 所有请求都带固定 `User-Agent`
- `Referer` 默认指向首页

异常策略：

- 单次请求失败时返回空结果，不向上抛出未处理异常
- 播放解析失败时回退为 `parse=1`
- 不实现自动重试和本地缓存

## 分类设计

首页分类固定为：

- `1 -> 电影`
- `2 -> 电视剧`
- `3 -> 综艺`
- `4 -> 动漫`
- `5 -> 短剧`

`homeContent` 返回：

- `class`

不返回筛选配置，因为参考实现里 `filterable = 0`，且 `getFilters()` 为空对象。

`homeVideoContent` 直接返回：

- `{"list": []}`

这样与仓库当前多数 Spider 的使用方式一致，避免把分类第一页混入首页推荐。

## 列表与搜索设计

分类列表 URL：

- `/type/<tid>-<page>.html`

搜索 URL：

- `/vodsearch/-------------.html?wd=<keyword>`

卡片解析统一抽到一个 helper 中，从页面结构提取：

- 标题：`a[title]`
- 链接：`a[href]`
- 海报：`.large[data-src]`
- 备注：`.small-text`

输出字段：

- `vod_id`
- `vod_name`
- `vod_pic`
- `vod_remarks`

分页返回字段：

- `page`
- `limit`
- `total`
- `list`

为了符合仓库约定，分类和搜索结果不返回 `pagecount`。由于页面没有稳定总页数，本次采用保守返回：

- `limit = len(list)`
- `total >= 当前页可见数量`

## 短 ID 设计

为了遵循仓库里的短 ID 约定，不对外暴露完整详情页和播放页 URL。

详情页短 ID：

- 原始路径：`/detail/<slug>.html`
- 对外格式：`detail/<slug>`

播放页短 ID：

- 原始路径：`/play/<id>.html`
- 对外格式：`play/<id>`

编码规则：

- 列表和搜索阶段把详情链接压成 `detail/...`
- 详情页播放列表把线路链接压成 `play/...`

解码规则：

- `detailContent` 先把 `detail/...` 还原成站点详情 URL
- `playerContent` 先把 `play/...` 还原成站点播放 URL

若传入的已经是完整 URL，则兼容直接使用，不额外报错。

## 详情页设计

详情解析基于详情页 HTML，输出单个视频对象，字段至少包含：

- `vod_id`
- `vod_name`
- `vod_pic`
- `type_name`
- `vod_actor`
- `vod_director`
- `vod_area`
- `vod_content`
- `vod_play_from`
- `vod_play_url`

字段提取策略：

- 标题：首个 `h1`
- 海报：详情主图 `img[src|data-src]`
- 类型、演员：从详情信息区链接提取
- 导演、地区：从对应文本块提取并清洗
- 简介：详情介绍段落文本

播放列表设计：

- 线路名来自 `.tabs.left-align a`
- 对应剧集来自同序号的 `.playno`
- 每条剧集拼接成 `剧集名$play/...`
- 每个线路内剧集用 `#` 连接
- 多线路之间用 `$$$` 连接

如果某个线路没有可用剧集，则跳过该线路，避免产生空分组。

## 播放解析设计

播放解析分三层，顺序与参考 JS 保持一致。

第一层，直接 JSON：

- 若播放页响应本身是 JSON
- 且 `code == 200` 且存在 `url`
- 则优先取 `url`

处理规则：

- `rose_` 前缀：先去掉前缀，再尝试 `decodeURIComponent + base64`，失败后回退普通 `base64`
- 相对路径：补成主站绝对 URL
- 成功后返回 `parse=0`

第二层，MacCMS player 配置：

- 从 HTML 中提取 `player_* = {...}`
- 读取 `url` 与 `encrypt`
- `encrypt == "1"` 时做 URL 解码
- `encrypt == "2"` 时先 URL 解码再 Base64 解码

若结果是直链，则返回：

- `parse=0`
- `jx=0`
- `url=<real_url>`

第三层，系统解析兜底：

- 当前两层都失败时
- 返回还原后的播放页 URL
- 设置 `parse=1`
- 设置 `jx=1`

所有成功分支默认附带站点头字段；直链分支的 `Referer` 指向站点首页。

## 测试设计

实现过程采用 TDD。测试文件为 `tests/test_乐兔.py`，先写失败测试，再写实现代码。

首轮测试覆盖：

- 首页分类返回固定 `type_id/type_name`
- 详情与播放短 ID 的编码和解码
- 分类列表卡片解析为统一字段
- 分类页 URL 组装正确
- 搜索 URL 正确并能解析结果
- 分类与搜索结果不包含 `pagecount`
- 详情页能提取元数据和多线路播放列表
- `detailContent` 会先把短 ID 还原成详情页 URL
- 播放解析支持纯 JSON 直链返回
- 播放解析支持 `rose_` 前缀解码
- 播放解析支持 MacCMS `encrypt=1`
- 播放解析支持 MacCMS `encrypt=2`
- 播放解析失败时回退系统解析

测试只使用内嵌 HTML/JSON 夹具和 mock 请求，不依赖真实网络。

## 验收标准

完成后应满足：

- 新增 `乐兔.py` 且不修改 `base/`
- 新增 `tests/test_乐兔.py`
- 分类、搜索、详情、播放四条主链路都可由单测覆盖
- 外部返回的详情和播放 ID 为短路径，不暴露完整 URL
- 分类和搜索结果不返回 `pagecount`
- 播放解析至少覆盖 JSON、`rose_`、MacCMS、兜底四类分支
