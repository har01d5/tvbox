# 魔方 APP Python 爬虫设计

## 目标

在当前 Python 仓库中新增一个符合 `base.spider.Spider` 接口的魔方 APP 爬虫，覆盖以下能力：

- 首页分类与筛选
- 分类列表
- 搜索
- 详情解析
- 播放解析

实现以用户提供的 Node/JS 版本为行为参考，但落地形式遵循当前仓库的单文件 Spider 约定。

## 范围

本次实现包含：

- 新增独立脚本，文件名为 `魔方APP.py`
- 使用魔方 APP 的 AES-CBC 接口协议
- 固定 host 为 `http://www.613mf4k12.top`
- 支持 `home/category/detail/search/player` 全链路
- 支持分类排序、分类屏蔽和分类重命名
- 支持地区融合和年份自动补充
- 支持线路排序、线路重命名和线路屏蔽
- 保留搜索验证码分支，并在需要时尝试 OCR
- 为新增行为补齐 `unittest`

本次实现不包含：

- 动态 `site` 下发 host
- Node/Fastify 路由层
- 真实 OCR 服务联调
- 修改 `base/` 公共层
- 多解析器 `auto` 优先级调度
- 本地缓存和重试机制

## 方案选择

采用仓库现有的“单站点单文件 + 单测”方案，并以 `黑猫APP.py` 的结构为底稿实现魔方版本。

选择该方案的原因：

- `黑猫APP.py` 已具备 AES、筛选、详情、播放的完整链路骨架
- 魔方的 JS 逻辑与黑猫同属 APP AES 接口族，迁移成本最低
- 本次任务目标是新增一个稳定 Spider，不是抽象公共基类

本次不抽取共享基类的原因：

- 会扩大改动面，增加回归范围
- 现有多个同类 Spider 仍有站点级差异，抽象收益不足
- 用户当前需求是尽快落地单蜘蛛实现

## 模块边界

新增脚本只在站点文件内部维护逻辑，不修改 `base/`。

脚本内部职责拆分如下：

- `init`
  - 初始化 host、API path、AES key/iv、UA、分类配置、地区融合配置、线路配置、搜索验证码状态
- `homeContent`
  - 拉取初始化接口，输出分类、筛选和首页推荐
- `homeVideoContent`
  - 返回空列表
- `categoryContent`
  - 请求分类筛选接口，必要时执行大陆地区聚合
- `searchContent`
  - 请求搜索接口，执行验证码处理与本地结果过滤
- `detailContent`
  - 请求详情接口并整理影片元数据与播放列表
- `playerContent`
  - 根据线路模式、解析类型和 `vodParse` 结果输出播放信息
- 私有辅助函数
  - AES 加解密
  - API 请求
  - 年份补全
  - 地区融合
  - 线路整理
  - 验证码获取与 OCR 文本修正

## Host 与请求策略

固定主域：

- `http://www.613mf4k12.top`

接口路径：

- `api=1`，因此实际请求路径为 `/api.php/getappapi.index/<endpoint>`

初始化与搜索端点默认值：

- `initV119`
- `searchList`

请求策略：

- 接口请求统一走 `POST`
- 请求头默认带 `User-Agent: okhttp/3.10.0` 和 `Accept-Encoding: gzip`
- 返回体中的 `data` 字段先做 AES-CBC 解密，再解析 JSON
- `version` 暂为空；只有后续站点明确要求时才注入

初始化策略：

- `init` 只做一次
- 通过初始化接口读取 `system_search_verify_status`
- 若该标记为真，则搜索前进入验证码分支

异常策略：

- 单次请求失败时尽量返回空结果，不向上抛出未处理异常
- 某个详情端点失败时允许切换备用端点继续尝试
- 播放解析失败时返回空 URL 或空列表，而不是抛异常

## 配置设计

站点文件内部维护默认配置对象，至少包含：

- `name`
- `url`
- `api`
- `dataKey`
- `dataIv`
- `init`
- `search`
- `version`
- `ua`
- `headers`
- `categories`
- `areaMerge`
- `ocr`

分类管理配置：

- `blockedNames = ["全部"]`
- `renameMap = {}`
- `forceOrder = ["电影", "连续剧", "综艺", "动漫", "短剧", "直播"]`

地区融合配置：

- `enabled = True`
- `displayName = "大陆"`
- `mergeList = ["中国大陆", "大陆", "内地"]`

OCR 配置：

- `enabled = False`
- `api = "http://154.222.22.188:9898/ocr/b64/text"`

线路管理配置：

- 以内置线路表匹配原始线路名
- 支持显示名、排序权重、解析模式、是否启用
- 直接使用用户提供的魔方线路表，包括禁用项如 `水印资源`、`YY`

## 分类与筛选设计

`homeContent` 的输入来源是初始化接口返回的 `type_list`。

分类处理规则：

- 屏蔽名称包含在 `blockedNames` 里的分类，例如 `全部`
- 对命中的分类名应用 `renameMap`
- 若配置了 `forceOrder`，则按配置顺序重排已保留分类

筛选转换规则：

- 将接口中的 `class/area/lang/year/sort` 转成仓库常用的筛选结构
- `sort` 对外统一映射为 `by`
- 显示名映射为 `类型/地区/语言/年份/排序`

特殊筛选处理：

- 地区筛选启用融合时，把 `中国大陆/大陆/内地` 合并显示为单个 `大陆`
- 年份筛选自动补入当前年份；若列表里无当前年份，则插入到 `全部` 后面

首页返回字段：

- `class`
- `filters`
- `list`

其中 `list` 直接复用初始化返回的分类推荐数据平铺结果。

## 列表与搜索设计

分类列表使用接口：

- `typeFilterVodList`

请求参数包括：

- `type_id`
- `page`
- `area`
- `year`
- `sort`
- `lang`
- `class`

对外筛选字段中的 `by` 在请求时还原成接口所需的 `sort`。

大陆地区融合开启且用户选择融合值时：

- 不直接请求一次 `area=大陆`
- 改为依次请求 `中国大陆/大陆/内地`
- 按 `vod_id` 去重后合并结果

搜索使用接口：

- `searchList`，也允许通过配置覆盖

搜索规则：

- 若初始化要求验证码，则在搜索前获取验证码图片、调用 OCR 并修正常见误识别字符
- 若 OCR 失败，则返回空列表，并附带错误消息
- 本地过滤掉 `vod_class` 包含 `屏蔽预留` 的结果
- 如果有搜索词，则只保留标题、备注或分类文本中包含关键词的结果
- 搜索结果映射为 `vod_id/vod_name/vod_pic/vod_remarks`
- `vod_remarks` 使用 `vod_year + vod_class` 拼接

分页返回字段遵循仓库当前约定：

- `page`
- `limit`
- `total`
- `list`

不返回 `pagecount`。

## 验证码设计

验证码仅在初始化标记要求时启用。

处理流程：

- 请求 `/verify/create?key=<uuid>` 获取图片
- 将图片转为 base64 文本
- 发送到 OCR 接口
- 对 OCR 返回文本执行字符替换修正
- 仅当结果是 4 位数字时才作为有效验证码提交

字符修正规则沿用参考 JS 中的映射，例如：

- `y -> 9`
- `口 -> 0`
- `q/u/o/d/D -> 0`
- `b -> 8`
- `已 -> 2`
- `五 -> 5`

实现要求：

- 优先使用标准库方式生成 `uuid`
- 测试中只验证本地逻辑与请求参数，不访问真实 OCR 服务

## 详情设计

详情优先尝试两个端点：

- `vodDetail`
- `vodDetail2`

详情字段映射：

- `vod_name`
- `vod_pic`
- `vod_remarks`
- `vod_content`
- `vod_actor`
- `vod_director`
- `vod_year`
- `vod_area`
- `vod_play_from`
- `vod_play_url`

数据整理规则：

- `vod_actor` 去掉前缀 `演员`
- `vod_director` 去掉前缀 `导演`
- `vod_year` 有值时补后缀 `年`

线路处理规则：

- 如果原始线路名含 `防走丢/群/防失群/官网`，则替换为递增兜底名 `1线/2线/...`
- 若线路名重复，则对重复项追加序号，避免冲突
- 若线路被配置为禁用，则直接跳过
- 每条线路按配置映射展示名与排序权重

播放串编码格式：

- `集名$线路名@@模式@@parse_api,url,token+,player_parse_type,parse_type`

输出时：

- `vod_play_from` 使用排序后的展示线路名，以 `$$$` 拼接
- `vod_play_url` 使用排序后的集列表，以 `$$$` 拼接

## 播放解析设计

`playerContent` 输入是详情阶段编码好的播放串。

处理顺序：

- 先解析出线路名、模式和载荷
- 若线路已禁用，直接返回空地址
- 当前只支持 `direct` 模式；`auto` 不实现动态 parser 调度

解析分支：

- `parse_type == "0"`
  - 直接返回解码后的原始播放地址
  - `parse = 0`，`jx = 0`
- `parse_type == "2"`
  - 返回 `parse_api + 播放地址`
  - `parse = 1`，`jx = 1`
- `player_parse_type == "2"`
  - 先请求 `parse_api + 播放地址`
  - 若响应 JSON 里存在 `url`，则直接返回该直链
- 其他情况
  - 对播放地址执行 AES 加密
  - 请求 `vodParse`
  - 从返回的 `json` 字段中提取最终地址

播放器返回结构沿用仓库现有 APP Spider 约定：

- `parse`
- `jx`
- `url`
- `header`

直连与需二次解析分支均带 Android/Dalvik UA 头；其余分支默认返回空 header。

## 测试设计

新增测试文件：

- `tests/test_魔方APP.py`

测试覆盖目标：

- AES 加解密可逆
- `_api_post` 能正确解密响应
- `homeContent` 会过滤分类、处理地区融合并补当前年份
- `categoryContent` 能正确映射 `by -> sort`
- `categoryContent` 在选择 `大陆` 时会多次请求并按 `vod_id` 去重
- `searchContent` 会过滤 `屏蔽预留` 且只保留关键词命中的结果
- 搜索验证码开启但 OCR 失败时返回空列表
- `detailContent` 会回退第二详情端点，并按线路规则构造 `vod_play_from` 与 `vod_play_url`
- `playerContent` 覆盖 `parse_type == 0`
- `playerContent` 覆盖 `parse_type == 2`
- `playerContent` 覆盖 `player_parse_type == 2`
- `playerContent` 覆盖 `vodParse` 回退分支

测试策略：

- 使用 `unittest` 和 `unittest.mock`
- 只 mock `fetch/post/_api_post` 等边界调用
- 不访问真实站点和 OCR 服务
- 先跑单模块测试，再视需要扩展到更大范围

## 验证计划

实现完成后的验证顺序：

1. `python -m unittest tests.test_魔方APP -v`
2. 如果实现过程中复用了或改动了相邻逻辑，再补跑相关模块测试

## 风险与取舍

主要风险：

- 魔方站点实际返回字段可能与参考 JS 记录存在细节差异
- 验证码图片格式或 OCR 服务返回格式可能不稳定
- 某些线路名可能与当前内置线路表存在别名差异

本次取舍：

- 优先保证与参考 JS 的主要行为一致
- 不为未使用的 `auto` 解析模式增加复杂度
- 不提前抽公共基类，避免影响其他 Spider
