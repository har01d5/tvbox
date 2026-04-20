# 欧歌接入玩偶聚合设计

**日期：** 2026-04-20

## 目标

在当前聚合蜘蛛 `py/玩偶聚合.py` 中新增 `欧歌` 站点配置，使其作为一个独立聚合站点参与首页分类、分类页抓取、搜索聚合和详情网盘线路合并。

本次工作同时要求：

- 保留独立单站 `py/欧歌.py`
- 不抽共享逻辑
- 不改变现有聚合接口
- 通过对应 `unittest`

## 范围

本次实现包含：

- 在 `py/玩偶聚合.py` 的 `self.sites` 中新增 `ouge` 站点
- 暴露 `site_ouge` 首页分类与 6 个固定分类筛选
- 支持欧歌分类页和搜索页 URL 模板
- 让欧歌参与现有聚合搜索与聚合详情
- 在 `py/tests/test_玩偶聚合.py` 中补充欧歌站点覆盖

本次实现不包含：

- 修改独立 `py/欧歌.py`
- 从独立 `欧歌.py` 复用配置或 helper
- 抽象新的公共站点基类
- 调整聚合结果的排序规则
- 修改其它现有站点的行为

## 方案选择

采用“最小配置接入，必要时增加最小站点兜底”的方案。

原因：

- 当前 `玩偶聚合.py` 已支持同类型网盘站的列表、搜索、详情与网盘线路整理
- 欧歌站点结构与现有聚合站的 HTML 结构兼容度较高
- 用户明确要求只接入新站，不抽共享层
- 最小接入可以把影响面控制在单个聚合文件和对应测试内

不采用“顺手与独立 `欧歌.py` 合并配置”的方案，因为会增加耦合和变更面，也不符合用户当前范围要求。

## 站点配置设计

新增站点定义：

- `id`: `ouge`
- `name`: `欧歌`
- `domains`: `["https://woog.nxog.eu.org"]`
- `filter_files`: `[]`

选择器与 URL 模板：

- `list_xpath`: `//*[contains(@class,'module-item')]`
- `search_xpath`: `//*[contains(@class,'module-search-item')]`
- `detail_pan_xpath`: `//*[contains(@class,'module-row-info')]//p`
- `category_url`: `/index.php/vod/show/id/{categoryId}/page/{page}.html`
- `search_url`: `/index.php/vod/search/page/{page}/wd/{keyword}.html`

默认分类完整沿用独立欧歌源：

- `("1", "电影")`
- `("2", "剧集")`
- `("3", "动漫")`
- `("4", "综艺")`
- `("5", "短剧")`
- `("21", "综合")`

这里故意不使用“欧歌电影”“欧哥剧集”这类首页展示名作为聚合过滤项值名，而是与现有聚合站点保持一致，使用更短的分类名称。

## 对外行为

### `homeContent`

新增 `site_ouge`：

- `class` 中出现 `{"type_id": "site_ouge", "type_name": "欧歌"}`
- `filters["site_ouge"]` 至少包含 `categoryId` 分组
- `categoryId` 的值顺序必须是：
  - 全部
  - 电影
  - 剧集
  - 动漫
  - 综艺
  - 短剧
  - 综合

不新增其它本地筛选项。

### `categoryContent`

对 `site_ouge`：

- 使用现有聚合接口 `categoryContent("site_ouge", pg, filter, extend)`
- 当 `extend` 中没有 `categoryId` 时，默认回退到欧歌首分类 `1`
- URL 组装规则为：
  - `/index.php/vod/show/id/{categoryId}/page/{page}.html`
- 列表卡片继续复用现有 `_parse_cards`

不为欧歌新增独立分类接口。

### `searchContent`

欧歌参与现有多站搜索流程：

- 站点搜索 URL 为 `/index.php/vod/search/page/{page}/wd/{keyword}.html`
- 搜索结果复用现有 `_parse_search_cards`
- 同名同年结果继续复用 `_aggregate_search_results`
- 聚合结果主信息仍由现有 `site_priority` 决定

不为欧歌新增独立搜索合并逻辑。

### `detailContent`

欧歌详情继续走现有聚合详情流程：

- `_fetch_site_detail` 使用站内短路径抓取详情页
- `_parse_detail_page` 提取元数据和网盘链接
- 欧歌站只贡献网盘分享链接，不参与站内播放解析
- 最终网盘线路继续进入聚合器现有 `vod_play_from` / `vod_play_url` 组装

## 排序与优先级

`site_priority` 中保留现有 `ouge` 位置，不调整其它站点排序：

- `wanou`
- `muou`
- `labi`
- `zhizhen`
- `erxiao`
- `huban`
- `kuaiying`
- `shandian`
- `ouge`

这样可以保证：

- 现有站点的主图、备注、主结果选择不发生变化
- 欧歌仅作为新补充来源参与聚合

## 错误处理

保持现有聚合器行为：

- 欧歌单站请求失败时，只影响该站，不中断整个聚合搜索
- 欧歌详情抓取失败时，跳过该站或返回空详情壳
- 站点 HTML 为空时，返回空列表或空网盘集合

不新增：

- 域名切换
- 重试
- 验证码绕过
- 浏览器执行

## 测试设计

仅补最小必要覆盖到 `py/tests/test_玩偶聚合.py`。

### 首页

新增断言：

- `site_ouge` 出现在 `homeContent(False)["class"]`
- `filters["site_ouge"][0]["value"]` 正确暴露 6 个分类

### 分类

新增测试：

- `categoryContent("site_ouge", "2", False, {})` 默认走欧歌分类模板
- 或者显式提供 `{"categoryId": "21"}` 时能正确拼接欧歌分类 URL
- 列表结果能解析出 `site:ouge:<detail_path>` 形式的 `vod_id`

### 搜索

新增测试：

- 欧歌站点能参与 `searchContent`
- 至少验证欧歌单站结果可被纳入聚合结果
- 不重复测试已有的聚合去重算法细节

### 详情

新增测试：

- 欧歌详情页提取出的网盘链接能被合并进聚合线路
- `vod_play_from` / `vod_play_url` 的格式继续符合现有聚合器约定

## 变更边界

本次改动应控制在：

- `py/玩偶聚合.py`
- `py/tests/test_玩偶聚合.py`
- 规格与计划文档

明确不修改：

- `py/欧歌.py`
- `py/tests/test_欧歌.py`
- `base/` 公共层

## 风险

- 欧歌站分类名与独立源首页文案略有差异：独立源是“欧歌电影/欧哥剧集”等，聚合过滤项采用短名称“电影/剧集”等；这是有意保持聚合 UI 一致性的选择
- 如果欧歌详情页字段结构和现有 `_parse_detail_page` 假设不完全一致，可能需要为欧歌补一个极小的专用兜底分支
- 现有聚合测试对搜索参与站数量可能较敏感，新增欧歌后需要避免把旧测试写死成固定调用次数

## 验收标准

满足以下条件即可视为完成：

- `玩偶聚合.py` 新增 `ouge` 站点配置
- `site_ouge` 在首页和筛选中可见
- 欧歌能参与分类页、搜索和详情聚合
- 独立 `欧歌.py` 继续保留且不受影响
- 新增/更新的 `tests/test_玩偶聚合.py` 通过
