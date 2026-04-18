# LibVIO Python 爬虫设计

## 目标

在当前 Python 仓库中新增一个符合 `base.spider.Spider` 接口的 LibVIO 站点爬虫，覆盖以下能力：

- 首页分类
- 首页近期列表
- 分类列表
- 详情页
- 搜索
- 播放解析

实现基于网页 DOM 抓取与播放页脚本解析，不依赖 Playwright，不修改 `base/` 公共层。

## 范围

本次实现包含：

- 新增独立脚本，暂定文件名为 `libvio.py`
- 使用单一站点主域：`https://libvio.site`
- 支持首页、分类、搜索、详情和站内播放解析

本次实现不包含：

- 多域名自动回退
- 网盘资源解析
- 大规模并发探测可播线路
- 通用资源站抽象框架

## 方案选择

采用混合方案：

- 列表、详情、搜索使用 `requests + lxml` 直接解析 HTML
- 播放解析吸收参考插件 `plugin_libvio` 中已验证的 `player_*` 配置、播放器 JS 和中间 API 解析逻辑

不直接逐行平移参考 JS，原因是：

- 当前仓库已有 Python 爬虫风格，宜保持单文件站点实现
- 参考 JS 中包含探测候选源、并发验证等偏重逻辑，Python 版先只保留稳定主链路
- 先满足常见播放线路的可维护实现，避免把站点特例扩散到整个仓库

## 模块边界

新增脚本只在站点文件内部维护逻辑，不修改 `base/`。

脚本内部职责拆分如下：

- `init`
  - 初始化主域、请求头、分类映射
- `homeContent`
  - 返回固定分类
- `homeVideoContent`
  - 抓取首页最近更新列表
- `categoryContent`
  - 请求分类页并解析媒体卡片
- `searchContent`
  - 请求搜索页并解析搜索结果
- `detailContent`
  - 提取影片基础信息和剧集列表
- `playerContent`
  - 解析剧集页中的 `player_*` 配置并拿到最终播放地址
- 私有辅助函数
  - URL 归一化
  - 列表卡片解析
  - 详情字段解析
  - 播放页配置提取
  - 播放器 JS 基址提取
  - API 播放地址提取

## Host 与分类策略

本次只实现单域：

- `https://libvio.site`

请求失败时不做多域切换，只返回空结果或空播放地址。

分类沿用参考插件配置：

- `index`
- `movie`
- `series`
- `anime`
- `jpandkr`
- `euandus`

分类 URL 映射如下：

- `index -> /`
- `movie -> /type/1-{pg}.html`
- `series -> /type/2-{pg}.html`
- `anime -> /type/4-{pg}.html`
- `jpandkr -> /type/15-{pg}.html`
- `euandus -> /type/16-{pg}.html`

其中：

- `homeContent` 返回上述固定分类
- `homeVideoContent` 抓取首页并提取最近更新条目

## 列表与搜索解析

### 首页与分类页

首页和分类页主要解析 `stui-vodlist__box` 卡片。

每张卡片提取规则：

- 链接：选择 `href` 含详情页路径的主链接
- 标题：优先链接 `title`，回退到节点文本
- 封面：优先 `data-original`，其次 `src`
- 描述：优先类名含 `pic-text` 的文本

输出字段：

- `vod_id`
  - 返回紧凑数字 id，不返回完整详情 URL
- `vod_name`
- `vod_pic`
- `vod_remarks`

列表解析时跳过明显网盘提示项，避免把不可直播资源混进常规列表。

### 搜索页

搜索 URL：

- `/search/-------------.html?wd=<keyword>`

搜索结果优先按首页同类卡片结构解析，保持输出字段与分类页一致。

### 分页策略

返回分页字段：

- `page = 当前页`
- `pagecount = pg + 1`，若当页无内容则为当前页
- `limit = 实际条目数`
- `total = 近似值`

不依赖站点总数统计。

## 详情页设计

`detailContent` 使用 `vod_id` 在内部组装详情页 URL 并请求页面。

提取字段：

- `vod_id`
- `path`
- `vod_name`
- `vod_pic`
- `vod_tag`
- `vod_time`
- `vod_remarks`
- `vod_play_from`
- `vod_play_url`
- `type_name`
- `vod_content`
- `vod_year`
- `vod_area`
- `vod_lang`
- `vod_director`
- `vod_actor`

不返回：

- `dbid`
- `type`

详情字段优先从详情主块中按标签解析，兼容纯文本行与结构化节点两种形式。

### 播放线路

播放列表只保留站内可播源：

- 解析 `stui-content__playlist`
- 跳过标题或分组中明显标识为网盘、夸克、UC 的资源
- `vod_play_from` 用 `$$$` 拼接线路名
- `vod_play_url` 用 `$$$` 对齐对应线路剧集

单个剧集项格式：

- `标题$播放id`

其中 `播放id` 为紧凑值，由 `playerContent` 再组装完整播放页 URL。

## 播放解析设计

LibVIO 播放解析核心不是详情页直链，而是播放页里的 `player_*` 配置和播放器脚本。

实现步骤：

1. 组装播放页 URL 并请求
2. 提取页面脚本中的 `player_*` JSON
3. 读取关键字段：
   - `url`
   - `from`
   - `link_next`
   - `id`
   - `nid`
4. 如果 `from` 属于网盘类（如 `kuake`、`uc`），直接返回空
5. 如果 `from` 是站点特殊源（如 `ty_new1`），按固定 API 模式请求
6. 否则请求 `/static/player/<from>.js`，提取播放器 API 基址
7. 根据不同源拼接 API 地址，再从 API 响应中抽取最终 `m3u8/mp4`

### API 响应解析

优先支持以下模式：

- JSON 或脚本内的 `url/urls` 字段
- 变量赋值中的 `m3u8/mp4` 直链
- `tweb` 之类需要二次解码的源，按参考实现做最小必要解码

如果最终 URL 仍是站内中间页，则允许一层站内跳转继续解析。

返回格式：

- `parse = 0`
- `playUrl = ""`
- `url = 最终播放地址`
- `header = {"User-Agent": "...", "Referer": "..."}`

## 请求与兼容性

统一请求头至少包含：

- 浏览器 `User-Agent`
- 需要时补 `Referer`

播放器 API 解析需要稳定 Referer，因此播放页与播放器 API 请求都应显式带站点 Referer。

本次优先采用无状态请求；如验证发现 LibVIO 对 cookie 敏感，再补最小 cookie 维护。

## 错误处理

实现遵循“失败返回空，不抛异常中断”的原则：

- 页面请求失败时返回空列表或空播放地址
- DOM 节点缺失时字段回退为空字符串
- 播放配置提取失败时尝试回退到直链正则
- 最终失败则返回 `{"parse": 0, "playUrl": "", "url": ""}`

日志只保留必要调试信息，主要用于播放解析链路。

## 测试设计

采用测试优先方式实现，先给纯解析函数写测试，再补生产代码。

测试重点：

1. 首页/分类卡片解析
   - 断言能从 `stui-vodlist__box` 提取详情 id、标题、封面和备注
2. 首页与分类高层流程
   - 断言 `homeContent` 返回固定分类
   - 断言 `homeVideoContent` 与 `categoryContent` 组装分页结果正确
3. 搜索解析
   - 断言能解析搜索列表并复用卡片解析
4. 详情解析
   - 断言基础字段提取正确
   - 断言会过滤网盘线路
   - 断言剧集列表输出为紧凑播放 id
5. 播放解析
   - 断言可从播放页提取 `player_*` 配置
   - 断言可从播放器 JS 提取 API 基址
   - 断言可从 API 或脚本提取最终 `m3u8/mp4`
   - 断言特殊源与空结果路径行为正确

优先使用 `unittest` 和 mock，避免测试依赖真实站点网络。

## 实施顺序

1. 新增 `tests/test_libvio.py`，先覆盖首页/分类/搜索/详情/播放器核心解析
2. 新增 `libvio.py` 基本骨架与分类映射
3. 实现首页、分类和搜索列表抓取
4. 实现详情字段和线路提取
5. 实现播放页配置解析与播放器 API 解析
6. 运行测试并补必要的站内跳转与特殊源兼容
