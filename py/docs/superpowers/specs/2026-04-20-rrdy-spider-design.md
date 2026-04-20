# 人人电影网 Python 爬虫设计

## 目标

在当前 Python 仓库中新增一个符合 `base.spider.Spider` 接口的人人电影网爬虫，覆盖以下能力：

- 首页分类
- 分类列表
- 搜索
- 详情解析
- 网盘线路直传

实现以用户提供的 JS 规则为行为参考，但落地形式遵循当前仓库的单文件 Spider 约定。

## 范围

本次实现包含：

- 新增独立脚本，文件名为 `人人电影网.py`
- 使用单一站点主域：`https://www.rrdynb.com`
- 支持 `home/category/detail/search/player` 主链路
- 首页返回固定四分类
- 详情页只保留网盘资源，不保留站内播放线路
- 为新增行为补齐 `unittest`

本次实现不包含：

- 保留或兼容 JS 版规则文件
- 修改 `base/` 公共层
- 站内播放页解析
- 迅雷与阿里网盘线路输出
- 在线联调、动态反爬处理、验证码处理

## 方案选择

采用仓库现有的“单站点单文件 + 单测”方案：

- 对外保持 `Spider` 接口兼容
- 对内拆分为 URL 拼接、标题清洗、列表卡片解析、详情解析、网盘识别几个 helper
- 不抽象新的通用基类，不修改现有公共逻辑

不直接保留 JS 版的原因是：

- 当前仓库消费的是 Python `Spider` 方法，不是 JS 插件接口
- 单文件 Spider 与现有仓库结构一致，测试也更直接
- 这次目标是把参考规则稳定映射到仓库约定，而不是双端维护

## 模块边界

新增脚本只在站点文件内部维护逻辑，不修改 `base/`。

脚本内部职责拆分如下：

- `init`
  - 初始化主域、请求头、固定分类
- `homeContent`
  - 返回固定四分类
- `homeVideoContent`
  - 返回空列表
- `categoryContent`
  - 请求分类页并返回分页结果
- `searchContent`
  - 请求搜索页并清洗高亮标题
- `detailContent`
  - 请求详情页并整理元信息和网盘线路
- `playerContent`
  - 对网盘分享链接直接透传
- 私有 helper
  - URL 组装
  - 文本与标题清洗
  - 列表卡片解析
  - 详情字段提取
  - 网盘链接筛选

## Host 与请求策略

本次只实现单域：

- `https://www.rrdynb.com`

请求策略：

- 所有 HTML 页面请求都走站点页面，不依赖隐藏接口
- 默认附带固定 `User-Agent`
- `Referer` 默认指向首页

异常策略：

- 单次请求非 200 时返回空结果，不向上抛出未处理异常
- 列表、搜索、详情局部字段缺失时尽量保留其余字段
- 不实现自动重试和本地缓存

## 分类设计

首页分类固定为：

- `movie/list_2 -> 电影`
- `dianshiju/list_6 -> 电视剧`
- `dongman/list_13 -> 动漫`
- `zongyi/list_10 -> 老电影`

`homeContent` 返回：

- `class`

不返回筛选配置，不扩展额外分类，保持与参考规则一致。

`homeVideoContent` 直接返回：

- `{"list": []}`

这样与仓库当前多数 Spider 的使用方式一致，避免把分类第一页混入首页推荐。

## ID 与 URL 设计

为了遵循仓库里的短 ID 约定，不对外暴露完整详情 URL。

详情页 ID 设计：

- 列表与搜索结果中的 `vod_id` 保留站内相对路径
- 示例：`/movie/12345.html`

解码规则：

- `detailContent` 先把相对路径拼回站点完整 URL
- 若传入值已经是完整 URL，则兼容直接使用

分类页 URL：

- `/{classPath}_{page}.html`
- 示例：`movie/list_2` 第 2 页请求 `https://www.rrdynb.com/movie/list_2_2.html`

搜索页 URL：

- `/plus/search.php?q=<keyword>&pagesize=10&submit=`
- 当页码大于 1 时追加 `&PageNo=<page>`

## 列表与搜索设计

分类页、搜索页都复用统一卡片解析 helper。

优先解析区域：

- `#movielist li`

卡片字段提取：

- 链接：优先取标题链接 `href`
- 标题：优先取 `title`，否则取链接文本或 HTML
- 海报：优先取懒加载 `data-original`，其次取 `src`
- 备注：取评分或备注文本

标题清洗规则：

- 去掉搜索高亮标签 `<font color='red'>` 和 `</font>`
- 若标题中存在 `《...》` 或 `「...」`，优先提取括号内文本
- 否则返回普通清洗文本

分页返回字段：

- `page`
- `limit`
- `total`
- `list`

为了符合仓库约定，分类和搜索结果不返回 `pagecount`。由于参考规则没有稳定总页数来源，本次采用保守返回：

- `limit = len(list)`
- `total = 当前页基础估算值或当前结果数`

## 详情页设计

详情解析基于详情页 HTML，输出单个视频对象，字段至少包含：

- `vod_id`
- `vod_name`
- `vod_pic`
- `vod_content`
- `vod_play_from`
- `vod_play_url`

字段提取策略：

- 标题：`.movie-des h1`
- 海报：`.movie-img img`
- 简介：`.movie-txt` 区域纯文本

网盘资源提取策略：

- 在 `.movie-txt` 内查找所有链接
- 只保留明确识别为网盘分享链接的 URL
- 显式过滤包含 `xunlei`、`aliyun`、`alipan` 的链接
- 其余非网盘普通链接一律忽略

详情页不输出站内播放线路。

若存在网盘链接，则统一组装为单条线路：

- `vod_play_from = 网盘`
- `vod_play_url = 名称$链接#名称$链接...`

名称优先使用链接文本；若为空，则回退为对应网盘名或通用标题。

若不存在任何可识别网盘链接：

- 保留基础元信息
- `vod_play_from` 和 `vod_play_url` 置空

## 网盘识别与播放设计

支持直接透传的网盘范围：

- 百度
- 夸克
- UC
- 115
- 123 盘
- 天翼
- 139

可通过域名关键字识别，例如：

- `pan.baidu.com`
- `pan.quark.cn`
- `drive.uc.cn`
- `115.com`
- `123pan.com`
- `cloud.189.cn`
- `yun.139.com`

排除范围：

- `pan.xunlei.com`
- `aliyundrive.com`
- `alipan.com`

`playerContent(flag, id, vipFlags)` 行为：

- 当 `id` 本身是受支持的网盘分享链接时，直接返回透传结果
- `parse = 0`
- `playUrl = ""`
- `url = 原始分享链接`
- 非网盘链接返回空 URL，明确表示本 Spider 不处理站内播放

## 容错策略

- 页面请求失败时，列表和搜索返回空列表，详情返回空字段对象
- 卡片缺少标题或链接时直接跳过，不产生脏数据
- 标题清洗失败时退回普通文本
- 单个网盘链接解析失败时跳过该链接，不影响其他链接输出
- 详情页没有网盘时不构造伪线路

## 测试设计

测试文件：

- `py/tests/test_人人电影网.py`

测试采用内嵌 HTML fixture 与 `unittest.mock`，不访问真实网络。

覆盖点：

1. 首页分类
   - 固定四分类输出正确
   - `homeVideoContent` 返回空列表

2. URL 与文本 helper
   - URL 组装能兼容相对路径和完整 URL
   - 标题清洗能处理高亮标签、`《》`、`「」` 和普通文本

3. 分类列表
   - 分类页 URL 按 `/{classPath}_{page}.html` 拼接
   - `#movielist li` 卡片能提取 `vod_id`、`vod_name`、`vod_pic`、`vod_remarks`
   - 返回结果不包含 `pagecount`

4. 搜索
   - 搜索 URL 正确
   - 第 2 页及以上会追加 `PageNo`
   - 搜索结果标题中的高亮标签会被清理

5. 详情
   - 能提取标题、海报、简介
   - 只保留允许的网盘链接
   - 过滤迅雷和阿里链接
   - 正确组装单条“网盘”线路

6. 播放
   - 网盘分享链接直接透传
   - 非网盘链接返回空 URL

## 成功标准

满足以下条件时，认为本次设计对应的实现完成：

- 新增 `人人电影网.py` 并符合仓库 `Spider` 接口
- 固定四分类、分类列表、搜索、详情和网盘透传链路可用
- 详情页只输出网盘线路，不输出站内播放线路
- 分类和搜索结果不返回 `pagecount`
- 单测覆盖上述主链路，且全部通过
