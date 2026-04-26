# 麦田影院 Python 爬虫设计

## 目标

在当前 Python 仓库中新增一个符合 `base.spider.Spider` 接口的麦田影院爬虫，实现用户给出的 JS 参考行为，并遵循仓库现有的单文件 Spider 与 `unittest` 测试约定。

本次实现范围：

- 固定分类首页
- 分类分页浏览
- 详情页元信息解析
- 详情页线路分组解析
- 播放页直链解析
- 无搜索占位返回

本次不实现：

- 首页推荐抓取
- 站点筛选项
- 模糊搜索或站外搜索
- 通用 MacCMS 基类抽象
- 超出参考 JS 的额外解密分支

## 方案选择

采用“单站点直解析 + 固定分类配置 + `player_data` / `art.php` 两段式解链”的实现。

原因如下：

- 用户已经给出完整的站点行为参考，直接映射到 Python 最稳妥
- 当前仓库的同类 Spider 以单文件实现为主，维护成本最低
- 该站详情页结构与现有 `耐视点播`、`糯米` 接近，可以复用相同的解析思路
- 搜索明确不做，没必要为了未来复用引入新的公共抽象

## 模块边界

新增 `py/麦田影院.py`，新增 `py/tests/test_麦田影院.py`，不修改 `py/base/`。

Spider 对外接口：

- `init`
- `getName`
- `homeContent`
- `homeVideoContent`
- `categoryContent`
- `searchContent`
- `detailContent`
- `playerContent`

Spider 内部 helper 负责：

- 统一请求头与绝对 URL 构造
- 文本清洗和短路径归一化
- 列表卡片解析
- 详情元信息解析
- 线路名与剧集分组解析
- `player_data` 提取与 JSON 解析
- `art.php` 两段式签名请求

## 站点配置

固定站点参数：

- `host`: `https://www.mtyy5.com`
- 固定桌面端 `User-Agent`
- 默认请求头包含 `Referer`、`Origin`、`User-Agent`

固定分类：

- `1` 电影
- `2` 电视剧
- `4` 动漫
- `3` 综艺
- `26` 短剧
- `25` 少儿

`homeContent` 返回固定分类，不抓取首页推荐。

`homeVideoContent` 固定返回 `{"list": []}`。

## 分类与卡片解析

分类 URL 固定为：

- `/vodshow/{type_id}--------{page}---.html`

列表解析规则：

- 遍历 `div.public-list-box`
- 取 `a.public-list-exp` 的 `href` 作为详情短路径
- 取 `a.public-list-exp` 的 `title` 作为片名
- 取 `img` 的 `data-src`，缺失时回退 `src`
- 取 `.public-list-prb` 文本作为备注
- `vod_id` 保留短路径，例如 `/voddetail/123.html`
- `vod_pic` 输出绝对 URL

返回结构：

- `page`
- `limit`
- `total`
- `list`

不返回 `pagecount`。

## 搜索策略

站点标题明确标注“无搜索”，因此 `searchContent` 不发起任何请求。

行为约束：

- 任意关键字都返回空结果
- 返回结构与仓库现有约定一致：`page`、`limit`、`total`、`list`

## 详情解析

详情页 URL：

- `host + vod_id`

基础信息：

- `vod_id`
- `vod_name`
- `vod_pic`
- `vod_content`
- `vod_remarks`

字段来源：

- 标题优先取页面 `h1`，缺失时回退详情 `title`
- 封面优先取详情图片区 `img`
- 简介优先取剧情介绍区文本，取不到时置空
- `vod_remarks` 取详情页状态类文本，缺失允许为空

播放分组规则：

- 先读取 `a.swiper-slide` 作为线路名来源
- 线路名去除数字字符后再清洗空白
- 再按页面顺序读取 `div.anthology-list-box`
- 每个 `anthology-list-box` 对应一个线路分组
- 分组内读取 `ul.anthology-list-play > li`
- 每个剧集项取文本作为名称
- 每个剧集项取第一个子元素的 `href` 作为播放短路径
- `vod_play_from` 与 `vod_play_url` 采用仓库统一的 `$$$` / `#` 拼接规则

如果线路名数量少于分组数量，缺失部分回退为 `线路{index}`。

## 播放解析

`playerContent` 只处理站内播放短路径。

播放页 URL：

- `host + play_id`

解析流程：

1. 请求播放页
2. 从脚本文本中提取 `player_data=...`
3. 解析 JSON，读取 `url`
4. 如果 `url` 已经是 `http` / `https` 直链，直接返回
5. 否则先对 `url` 执行 URL 解码，再请求：
   - `/static/player/art.php?get_signed_url=1&url=<decoded>`
6. 解析上一步 JSON 中的 `signed_url`
7. 再请求：
   - `/static/player/art.php<signed_url>`
8. 从返回 JSON 中读取 `jmurl` 作为最终媒体地址

返回结构：

- 成功时返回 `parse=0`、`jx=0`、`playUrl=""`、`url=<media_url>`、`header=<请求头>`
- 失败时回退返回 `parse=1`、`jx=1`、`playUrl=""`、`url=<完整播放页地址>`、`header=<请求头>`

请求头约束：

- 最终播放结果保留桌面端 `User-Agent`
- `Referer` 指向播放页 URL

## 数据约束

ID 设计遵循仓库现有习惯：

- `vod_id` 使用详情短路径
- 播放项 ID 使用播放短路径
- 不把站内详情 URL 或播放 URL 预先展开写入 ID

结果约束：

- `vod_pic` 尽量输出绝对地址
- 列表、分类、搜索不返回 `pagecount`
- 搜索不触网
- 解析失败尽量返回空结果或解析页回退，而不是抛异常

## 测试策略

采用 TDD，先新增 `py/tests/test_麦田影院.py`，再实现 Spider。

测试覆盖最小闭环：

- `homeContent` 返回固定分类
- `homeVideoContent` 返回空列表
- `categoryContent` 构造正确 URL 并解析卡片
- `searchContent` 对任意关键字返回空结果且不触网
- `detailContent` 按 `swiper-slide + anthology-list-box` 组装播放分组
- `playerContent` 覆盖直链分支
- `playerContent` 覆盖 `art.php` 两段式解签分支
- `playerContent` 在脚本缺失或 JSON 无效时回退解析页
