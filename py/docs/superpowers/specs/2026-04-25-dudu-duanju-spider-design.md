# 嘟嘟短剧 Python 爬虫设计

## 目标

在当前 Python 仓库中新增一个符合 `base.spider.Spider` 接口的 `嘟嘟短剧` 爬虫，对接 `https://api-v2.cenguigui.cn/api/duanju.html`，支持首页、分类、搜索、详情和播放。

## 范围

本次实现包含：

- 新增 `py/嘟嘟短剧.py`
- 新增 `py/tests/test_嘟嘟短剧.py`
- 固定分类列表
- 分类、搜索、详情与播放 API 对接
- 标题清洗与多清晰度播放地址选择

本次实现不包含：

- 修改 `py/base/` 公共层
- 改造 `py/短剧优选.py`
- 新增真实联网测试
- 引入缓存、代理或登录逻辑

## 方案

采用“单 Spider 文件 + API helper + 离线 JSON 测试”的方案。

原因：

- 用户目标是新增独立爬虫，不是替换聚合源
- 目标站点是 JSON API，核心工作是请求构造和字段映射，不需要 HTML 解析
- 仓库现有测试体系适合用 `unittest + mock` 固定接口响应

## 接口映射

- `homeContent`
  - 返回固定分类列表
- `homeVideoContent`
  - 请求 `?name=热播&page=1`
  - 将返回列表映射为首页推荐
- `categoryContent`
  - 请求 `?name=<分类名>&page=<页码>`
  - 返回列表、`page`、`limit`、`total`
  - 不额外引入复杂分页推断，仅在当前页有结果时维持最小可翻页行为
- `searchContent`
  - 请求 `?name=<关键词>&page=<页码>`
  - 与分类复用同一列表映射
- `detailContent`
  - 请求 `?id=<剧集ID>`
  - 将分集数组整理为单线路 `嘟嘟短剧`
  - 使用 `video_id` 作为播放条目 ID
- `playerContent`
  - 请求 `?video_id=<分集video_id>`
  - 对 `qualities` 按画质优先级排序并返回直链

## 数据约定

- `vod_id` 使用 API 返回的剧目 `id`
- `vod_name` 对标题做轻量清洗，移除如 `【热播】`、`【新剧】` 等标签
- `vod_pic` 使用 `cover`
- `vod_remarks` 优先使用总集数，格式为 `更新至N集`
- `vod_play_from` 固定为 `嘟嘟短剧`
- `vod_play_url` 使用 `集名$video_id` 形式拼接
- `playerContent` 优先返回更高清晰度地址，优先级为 `1080p > sc > sd`

## 错误处理

- 请求非 2xx 或 JSON 解析失败时，列表接口返回空列表
- 详情失败时返回空 `list`
- 播放失败时返回 `parse=0` 且 `url` 为空字符串
- 尽量把错误限制在当前接口，不影响其他入口

## 测试策略

使用嵌入式 JSON 夹具和 mock 覆盖：

- 首页分类与首页推荐
- 分类请求参数与列表映射
- 搜索空关键字与正常搜索
- 标题清洗逻辑
- 详情页分集整理与基础元数据
- 播放画质排序与直链输出
- 请求失败时的空结果回退
