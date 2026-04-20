# 玩偶哥哥 Python 爬虫设计

## 目标

在当前 Python 仓库中新增一个独立单站蜘蛛 `py/玩偶哥哥.py`，参考用户提供的 JS 版本行为，实现符合 `base.spider.Spider` 接口的网盘资源站适配。

本次实现需要覆盖：

- 首页 8 个固定分类
- 分类列表
- 搜索
- 详情解析
- 网盘线路组织
- 播放透传
- 对应 `unittest`

## 范围

本次实现包含：

- 新增独立蜘蛛文件 `py/玩偶哥哥.py`
- 新增测试文件 `py/tests/test_玩偶哥哥.py`
- 单域名站点适配：`http://wogg.xxooo.cf`
- 固定 8 个分类，分类 ID 与参考 JS 保持一致
- 分类页和搜索页卡片解析
- 详情页元数据与网盘链接提取
- 按网盘类型输出 `vod_play_from` 和 `vod_play_url`
- `playerContent` 对已识别网盘分享链接直接透传

本次实现不包含：

- 聚合多站
- 本地筛选配置文件
- 站内视频播放解析
- 验证码、浏览器执行或复杂反爬绕过
- 修改 `base/` 公共层

## 方案选择

采用“单站单文件 + 单测”的现有仓库模式，而不是复用 `玩偶聚合.py` 的聚合结构。

原因：

- 用户明确要求独立单站
- 参考 JS 本身就是单站逻辑
- 独立站不需要聚合 ID、跨站去重和主次站排序
- 单站实现更容易保持接口简单，测试也更聚焦

## 接口设计

### `homeContent`

返回 8 个固定分类：

- `1 -> 玩偶电影`
- `2 -> 玩偶剧集`
- `3 -> 玩偶动漫`
- `4 -> 玩偶综艺`
- `44 -> 臻彩视界`
- `6 -> 玩偶短剧`
- `5 -> 玩偶音乐`
- `46 -> 玩偶纪录`

不返回筛选项。

### `homeVideoContent`

返回空列表：

- `{"list": []}`

### `categoryContent`

分类页 URL 规则：

- `/vodshow/{tid}--------{page}---.html`

解析页面中的卡片，输出：

- `vod_id`
- `vod_name`
- `vod_pic`
- `vod_remarks`

分页返回字段：

- `page`
- `limit`
- `total`
- `list`

不返回 `pagecount`，以保持当前仓库对新蜘蛛的约定。

### `searchContent`

搜索 URL 规则：

- `/vodsearch/-------------.html?wd={keyword}&page={page}`

空关键词直接返回空列表。

搜索结果结构与分类列表保持一致。

### `detailContent`

通过详情页提取：

- `vod_id`
- `vod_name`
- `vod_pic`
- `vod_year`
- `vod_director`
- `vod_actor`
- `vod_content`
- `vod_play_from`
- `vod_play_url`

不解析站内播放页，只整理网盘分享链接。

### `playerContent`

若 `id` 是支持的网盘分享链接，则返回透传结果：

```python
{"parse": 0, "playUrl": "", "url": id}
```

若不是已识别网盘链接，则返回空 URL：

```python
{"parse": 0, "playUrl": "", "url": ""}
```

## 模块边界

新蜘蛛内部拆分为以下职责：

- 站点配置与固定分类
- URL 组装
- 文本清洗
- 图片 URL 修正
- 列表卡片解析
- 搜索卡片解析
- 详情页字段提取
- 网盘类型识别
- 网盘线路拼接

不新增公共基类，不抽共享模块。

## URL 与 ID 设计

详情页 `vod_id` 使用站内短路径，而不是完整 URL。

编码方式：

- 详情链接 `/voddetail/123.html` 对外直接保存为 `/voddetail/123.html`

原因：

- 与参考 JS 行为一致
- 当前仓库已有多个蜘蛛直接使用站内短路径作为 `vod_id`
- 单站实现不需要再引入额外编码层

详情请求时再基于主域拼成完整地址。

## 请求策略

主域固定为：

- `http://wogg.xxooo.cf`

请求头包含固定 `User-Agent`，必要时补 `Referer` 为首页。

异常处理策略：

- 页面请求失败时返回空列表或空字段结果
- 不向上抛出未处理异常
- 不实现多域名切换
- 不实现重试

## 图片修正规则

保留参考 JS 的核心行为：

- 空图片返回空字符串
- 以 `/db.php?url=` 开头的图片地址补全为绝对地址
- 若命中百度 `gimg` 包裹且 `src=` 后是 `data:image/`，则视为无效图片并返回空字符串
- 其他情况下保留原值，必要时补全为绝对地址

这样可以兼容站点现有的懒加载和图片代理形式。

## 列表与搜索解析

分类列表解析容器：

- `#main .module-item`

提取策略：

- 链接：`.module-item-pic a[href]`
- 标题：`.module-item-pic img[alt]`
- 封面：`.module-item-pic img[data-src|src]`
- 备注：`.module-item-text`

搜索结果解析容器：

- `.module-search-item`

提取策略：

- 链接和标题优先来自 `.video-serial`
- 封面来自 `.module-item-pic img[data-src|src]`
- 备注优先取 `.video-serial` 文本，缺失时回退 `.module-item-text`

列表和搜索都应避免空标题、空链接项。

## 详情解析

详情页从 HTML 中提取以下信息：

- 标题：`.page-title`
- 封面：`.mobile-play .lazyload[data-src|src]`
- 年份、导演、主演：遍历 `.video-info-itemtitle` 与相邻内容节点
- 简介：优先从“剧情”字段或对应文本块提取
- 网盘链接：`.module-row-info p`

字段处理规则：

- 多个导演或主演用英文逗号连接
- 去除多余空白字符
- 缺失字段保留空字符串

## 网盘线路设计

详情页中每个分享链接会被识别为网盘类型，再输出为播放线路。

首批支持识别：

- 百度网盘
- 夸克网盘
- UC 网盘
- 阿里云盘
- 迅雷云盘
- 115 网盘
- 天翼云盘
- 139 网盘
- 123 云盘

输出规则：

- `vod_play_from` 中每条线路格式为 `<pan_type>#玩偶哥哥`
- `vod_play_url` 中每条线路格式为 `<资源标题>$<分享链接>`
- 线路之间使用 `$$$` 分隔
- 单站内对重复分享链接去重
- 同一详情页内按预设网盘优先级排序

资源标题使用人类可读名称，例如：

- `百度资源`
- `夸克资源`
- `阿里资源`

## 测试设计

先写失败测试，再补实现。

测试覆盖范围：

- `homeContent` 返回 8 个固定分类
- `categoryContent` 正确拼接分类 URL 并解析卡片
- `searchContent` 对空关键词返回空列表
- `searchContent` 正确解析搜索结果
- 图片修正逻辑覆盖代理图和无效百度图
- `detailContent` 提取标题、封面、年份、导演、主演、简介和网盘链接
- 网盘线路按类型识别、去重和排序
- `playerContent` 对网盘链接透传
- `playerContent` 拒绝非网盘链接

测试全部使用内联 HTML 和 `unittest.mock`，不依赖真实网络。

## 风险与取舍

主要风险：

- 参考域名可能失效，但不影响离线测试与结构实现
- 页面字段“剧情”区块结构可能存在变体，需要解析逻辑适度宽松
- 搜索结果中部分元素可能不是标准 `a` 标签，需要兼容从属性和文本双路径提取

本次取舍：

- 优先实现与参考 JS 一致的静态 HTML 解析
- 不在首版里扩展筛选或多域名容灾
- 不实现任何超出网盘透传范围的播放解析
