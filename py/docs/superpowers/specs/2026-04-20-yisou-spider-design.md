# 奕搜 Python 爬虫设计

## 目标

在当前 Python 仓库中新增一个符合 `base.spider.Spider` 接口的奕搜站点爬虫，覆盖以下能力：

- 首页分类
- 分类列表
- 搜索
- 详情解析
- 网盘透传播放

实现以用户提供的 JS 版本为行为参考，但最终产物遵循当前仓库的单文件 Spider 约定，并对齐仓库中现有网盘类规则的输出格式。

## 范围

本次实现包含：

- 新增独立脚本，文件名为 `奕搜.py`
- 使用单一站点主域：`https://ysso.cc`
- 支持 `home/category/detail/search/player` 主链路
- 首页返回固定分类
- 详情页提取影片元数据和网盘分享链接
- `playerContent` 对分享链接做原样透传
- 为新增行为补齐 `unittest`

本次实现不包含：

- 参考 JS 中的 `panUrls` 返回格式复刻
- 站内播放线路解析
- 网盘驱动匹配、提取码自动补链或网盘二次解析
- 浏览器执行、反爬绕过或多域名探活
- 修改 `base/` 公共层

## 方案选择

采用仓库现有的“单站点单文件 + 单测”方案：

- 对外保持 `Spider` 接口兼容
- 对内拆分为 URL 组装、文本清洗、标题备注提取、列表解析、详情页元信息提取和网盘分组几个 helper
- 保留参考 JS 的核心页面解析行为，但输出改为仓库现有 Spider 可直接消费的 `vod_play_from` / `vod_play_url`

不直接照搬参考 JS 返回 `panUrls` 的原因是：

- 当前 Python 仓库上层消费的是标准播放线路字段
- 仓库里已有网盘透传型 Spider 可以直接复用输出约定
- 本次目标是把网页上的网盘资源稳定映射到现有播放器接口，而不是维持 JS 私有数据结构

## 模块边界

新增脚本只在站点文件内部维护逻辑，不修改 `base/`。

脚本内部职责拆分如下：

- `init`
  - 初始化主域、请求头和固定分类
- `homeContent`
  - 返回固定 `class`
- `homeVideoContent`
  - 返回空列表
- `categoryContent`
  - 请求分类页并解析卡片列表
- `searchContent`
  - 请求搜索页并解析卡片列表
- `detailContent`
  - 请求详情页，提取影片元数据与网盘分享链接
- `playerContent`
  - 对网盘分享链接或 `push://` 地址做原样透传
- 私有辅助函数
  - 补全绝对 URL
  - 清洗标题文本
  - 从标题中提取备注
  - 解析列表卡片
  - 解析详情元信息
  - 识别网盘类型并构造播放分组

## Host 与请求策略

本次只实现单域：

- `https://ysso.cc`

请求统一通过 `self.fetch` 发起，固定请求头至少包含：

- `User-Agent`
- `Referer`

请求原则：

- HTML 请求超时固定为 10 秒
- 请求失败时返回空 HTML 或空结果，不抛出未处理异常
- 不引入额外缓存、重试或 JS 执行环境

## 分类设计

首页分类固定为：

- `dy -> 电影`
- `dsj -> 电视剧`
- `zy -> 综艺`
- `dm -> 动漫`
- `jlp -> 纪录片`
- `dj -> 短剧`

`homeContent` 返回：

- `class`

不返回筛选配置，因为参考实现没有分类筛选结构。

`homeVideoContent` 直接返回：

- `{"list": []}`

## 列表与搜索设计

分类页 URL：

- `/<classId>.html?page=<page>`

搜索 URL：

- `/search.html?keyword=<urlencoded keyword>&page=<page>`

分类页和搜索页共用同一个卡片解析器，目标结构为 `.list-boxes`。

卡片字段提取规则：

- `vod_id`
  - 优先取 `a.text_title_p[href]`
  - 如果缺失则回退 `.left_ly a[href]`
  - 输出站点短路径，不暴露完整详情 URL
- `vod_name`
  - 使用标题文本清理 `[]` 标签后的结果
- `vod_pic`
  - 取 `img.image_left[src]` 并补全成绝对地址
- `vod_remarks`
  - 优先从标题中的 `[]` 标签提取
  - 若无可用备注，则回退 `.list-actions span`

标题备注提取顺序与参考 JS 保持一致：

1. 更新集数，如 `[更12]` 转成 `更新至12集`
2. 评分，如 `[8.5分]` 转成 `评分:8.5`
3. 年份，如 `[2025]` 转成 `首播:2025`

分页返回字段：

- `page`
- `limit`
- `total`
- `list`

为了符合仓库当前约定，分类和搜索结果不返回 `pagecount`。

## 短 ID 设计

为了遵循仓库里的短 ID 规则，不对外暴露完整详情页 URL。

列表与搜索阶段拿到的详情链接如果为站内 URL，则统一压缩为站点相对路径，例如：

- `/resource/12345`

`detailContent` 接收到相对路径后再补成完整详情 URL。

如果上层传入的是完整 URL，也兼容直接处理，但 Spider 自身产出仍以短路径为主。

## 详情页设计

详情页输出单个视频对象，字段至少包含：

- `vod_id`
- `vod_name`
- `vod_pic`
- `vod_remarks`
- `vod_director`
- `vod_actor`
- `vod_content`
- `vod_play_from`
- `vod_play_url`

元信息提取规则：

- 标题
  - `h1.articl_title`
  - 标题中的 `[]` 标签会先用于生成 `vod_remarks`，再从标题中剥离
- 封面
  - `.tc-box.article-box img` 首张图
- 导演与编剧
  - 遍历 `#info > span`
  - 命中“导演”或“编剧”标签时，读取 `.attrs a`
  - 去重后以 `, ` 拼接到 `vod_director`
- 主演与演员
  - 命中“主演”或“演员”标签时，读取 `.attrs a`
  - 去重后以 `, ` 拼接到 `vod_actor`
- 简介
  - 遍历正文中长度明显大于标签名的段落
  - 取首个有效长文本并压缩空白

提取码策略：

- 从整页文本中匹配 `提取码[:：]XXXX`
- 若命中，则追加到 `vod_remarks`
- 不把提取码写回网盘链接，不做自动拼装

## 网盘资源设计

详情页只保留网盘分享资源，不保留站内播放线路。

网盘链接提取策略：

- 遍历详情页中所有 `a[target="_blank"][href]`
- 仅保留 `http/https` 绝对地址
- 按分享链接去重，避免同链接多次输出

网盘类型识别范围：

- `baidu`
  - `pan.baidu.com`
- `quark`
  - `pan.quark.cn`
- `uc`
  - `drive.uc.cn`
- `aliyun`
  - `alipan.com`
  - `aliyundrive.com`
- `xunlei`
  - `pan.xunlei.com`

输出策略：

- 能识别盘类型时，按盘类型分组输出
- 每个分组的单条资源格式为 `<盘名>$<分享链接>`
- 同一分组内多条资源用 `#` 连接
- 多个分组之间用 `$$$` 连接
- `vod_play_from` 与 `vod_play_url` 的分组顺序保持一致

盘类型排序优先级：

1. `baidu`
2. `quark`
3. `uc`
4. `aliyun`
5. `xunlei`

如果详情页存在外链但都不属于上述已识别网盘：

- 使用单一兜底线路名 `奕搜`
- 对应 `vod_play_url` 为 `1$push://<url>#2$push://<url>...`

如果详情页不存在任何可用外链：

- `vod_play_from = 奕搜`
- `vod_play_url = ""`

这样可以保持与仓库里现有网盘透传规则一致，并且明确表达“本 Spider 只提供网盘分享链接透传”。

## 播放设计

`playerContent(flag, id, vipFlags)` 不做二次解析，只负责规范化透传：

- 如果 `id` 以 `push://` 开头
  - 去掉前缀后返回真实分享链接
- 如果 `id` 已经是 `http/https` 分享链接
  - 直接原样返回
- 其他情况
  - 也原样返回，不额外猜测和改写

返回结构：

- `parse = 0`
- `url = <透传后的值>`

不附加鉴权头，不做 `jx` 回退。

## 错误处理

- 分类页、搜索页请求失败时返回空列表
- 详情页请求失败时返回 `{"list": []}`
- 单个网盘链接识别失败时跳过盘类型识别，但不影响其他链接
- 标题、图片、导演、主演、简介等字段缺失时返回空字符串

## 测试设计

测试覆盖以下行为：

1. `homeContent`
   - 断言固定分类完整且顺序正确
2. 列表解析
   - 断言能从 `.list-boxes` 解析短路径 `vod_id`、清洗后的标题、图片和备注
   - 断言备注提取优先级符合参考 JS
3. `categoryContent`
   - 断言分类页 URL 正确
   - 断言返回字段不包含 `pagecount`
4. `searchContent`
   - 断言空关键词返回空列表
   - 断言搜索 URL 包含 URL 编码后的关键词
5. `detailContent`
   - 断言能提取标题、图片、导演、主演、简介和提取码
   - 断言详情页只输出网盘透传线路
   - 断言网盘链接按盘类型分组、去重和排序
   - 断言未识别外链时回退到 `push://` 兜底线路
6. `playerContent`
   - 断言 `push://` 去壳透传
   - 断言普通网盘分享链接原样透传

## 验收标准

- `homeContent/categoryContent/detailContent/searchContent/playerContent` 均返回符合当前项目习惯的数据结构
- 列表和搜索结果只输出站点短路径 `vod_id`
- 标题备注提取和标题清洗与参考 JS 的优先级一致
- 详情页只输出网盘分享线路，不保留站内播放线路
- `playerContent` 对网盘链接仅做原样透传
- 新增 `unittest` 能稳定覆盖主要解析分支
