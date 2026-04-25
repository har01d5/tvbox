# SecSpider 加密插件设计

## 目标

为当前 Spider 插件体系设计一套可落地的“源码封包”机制，用于隐藏 Spider 明文源码，避免普通用户直接打开插件文件即可看到实现细节。

本次设计面向的宿主前提如下：

- 宿主支持修改加载流程
- 插件既可能来自本地文件，也可能来自远程下载
- 宿主本身是开源可见、运行在用户设备上的 Python 客户端
- 现有 Spider 插件接口保持不变，仍以 `Spider` 类作为宿主入口

本次设计的核心目标是：

- 让发布物不再是直接可读的 Python 明文源码
- 支持宿主对插件做来源校验和完整性校验
- 在不改变 Spider 对外接口的前提下完成加载
- 保持明文插件与加密插件双栈兼容，便于渐进迁移

本次设计不追求：

- 防住能修改宿主、抓内存、下断点的逆向者
- 做在线授权平台
- 做设备绑定、过期控制或远程吊销
- 让用户设备上的插件“不可提取”

## 背景与边界

当前宿主 `SpiderPluginLoader` 使用 `importlib.util.spec_from_file_location(...)` 直接执行本地 Python 文件，并约定模块中导出 `Spider` 类。该机制适合明文源码插件，但不适合密文封包。

由于本次目标是隐藏源码而不是彻底防逆向，设计必须先承认以下边界：

- 只要插件最终要在本地运行，明文源码或等价字节码一定会在某个时刻进入解释器
- 解密端开源且跑在用户设备上，因此任何宿主内置密钥都可能被逆向提取
- 这意味着方案的安全收益是“提高获取源码的门槛”，而不是“保证源码永不泄露”

因此，本次设计定位为：

- 源码封包机制
- 完整性与签名校验机制
- 宿主侧双栈插件加载机制

而不是 DRM 或不可导出的执行环境。

## 方案选择

候选方案：

1. 纯混淆方案
2. 离线封包 + 本地验签 + 本地解密方案
3. 在线授权下发解密材料方案

选用方案 2。

原因：

- 用户当前目标只是避免普通用户直接看源码，不需要引入在线依赖
- 宿主已允许修改，适合增加自定义 loader
- 本地验签可以防止第三方伪造或篡改插件
- 双栈方案能平滑兼容现有明文插件生态
- 相比在线授权，工程复杂度和运维成本更可控

不选方案 1 的原因：

- 只能防止双击直读，无法提供可靠的篡改检测
- 无法建立统一的协议版本、密钥轮换和签名链路

不选方案 3 的原因：

- 超出当前目标
- 需要额外服务端、授权链路和可用性保障

## 总体架构

系统分成三个角色：

- `builder`
  - 读取明文 Spider 源码
  - 生成内容密钥
  - 加密源码
  - 生成签名
  - 输出单文件加密包
- `loader`
  - 读取插件文件
  - 识别明文或密文格式
  - 对密文包执行验签、解密、内存加载
- `runtime spider`
  - 解密后在内存中编译执行
  - 对宿主继续暴露 `Spider` 类

总体链路如下：

1. 构建阶段读取明文 Spider 源码
2. 生成随机内容密钥 `content_key`
3. 用 `content_key` 对源码做对称加密
4. 使用宿主密钥派生链路包裹 `content_key`
5. 对包头和密文内容做签名
6. 产出单文件文本封包
7. 宿主加载时先识别格式
8. 若为明文插件，则继续按现有 `importlib` 逻辑执行
9. 若为密文插件，则先验签，再解包内容密钥，再解密源码
10. 解密后的源码通过 `compile/exec` 在内存中执行
11. 宿主统一从模块中读取 `Spider` 类并实例化

## 封包格式设计

建议定义文本协议 `secspider/1`，保持现有注释头风格，便于远程分发和人工排查。

推荐格式：

```text
// ignore
//@name:[直] omofun
//@webSite:http://101.42.227.94:11024
//@version:1
//@remark:
//@codeID:z5nxgZSWE8ipZYvGtImsRFu73TOB45fZ
//@env:
//@isAV:0
//@deprecated:0
//@order:B
//@format:secspider/1
//@alg:aes-256-gcm
//@wrap:hkdf-aes-keywrap
//@sign:ed25519
//@kid:k2026_04
//@nonce:base64:...
//@ek:base64:...
//@hash:sha256:...
//@sig:base64:...
// ignore
payload.base64:...
```

字段分组如下：

- 业务元数据
  - `name`
  - `webSite`
  - `version`
  - `remark`
  - `codeID`
  - `env`
  - `isAV`
  - `deprecated`
  - `order`
- 协议元数据
  - `format`
  - `alg`
  - `wrap`
  - `sign`
  - `kid`
- 加密与校验字段
  - `nonce`
  - `ek`
  - `hash`
  - `sig`
- 数据字段
  - `payload.base64`

字段约束如下：

- `format` 固定为 `secspider/1`
- `alg` 首版固定为 `aes-256-gcm`
- `wrap` 首版固定为 `hkdf-aes-keywrap`
- `sign` 首版固定为 `ed25519`
- `kid` 表示当前包使用的密钥版本
- `nonce` 为内容加密随机数
- `ek` 为包裹后的内容密钥，不是主密钥本身
- `hash` 为解密前明文源码的 `sha256`
- `sig` 覆盖除 `sig` 自身外的所有头字段和 `payload`

`payload.base64` 存放最终密文载荷，推荐流程为：

- 明文源码转 `utf-8` 字节
- 可选压缩
- 使用内容密钥加密
- 对结果做 `base64` 编码

## 算法选择

首版固定采用如下组合：

- 内容加密：`AES-256-GCM`
- 内容密钥派生：`HKDF-SHA256`
- 发布签名：`Ed25519`

选择原因如下：

- `AES-256-GCM` 为成熟 AEAD 算法，适合同时提供保密性和密文完整性
- `HKDF-SHA256` 足够简单，适合从宿主主密钥按 `kid/codeID/version` 派生包密钥
- `Ed25519` 适合快速、稳定地完成离线签名和验签

本次设计明确不采用：

- 自定义异或或字符串切片混淆
- 自研加解密协议
- 只做加密不做签名

## 密钥分层设计

宿主开源且运行在用户设备上，因此密钥体系的设计目标不是“绝对保密”，而是避免所有插件共用一把固定明文密钥。

推荐分三层密钥：

### 1. 发布签名密钥对

- 构建环境持有 `Ed25519 private key`
- 宿主持有对应 `Ed25519 public key`

用途：

- 证明插件确实由发布方签发
- 拦截被篡改或伪造的插件包

约束：

- 私钥绝不进入客户端

### 2. 宿主主密钥

- 宿主内置 `master_secret`
- 不直接用于解密 `payload`

用途：

- 派生当前包使用的 `wrap_key`

说明：

- 这层密钥会被逆向到，因此安全作用有限
- 但仍优于“所有插件共用固定 AES key”的做法

### 3. 内容密钥

- 每个插件构建时随机生成一个 32 字节 `content_key`

用途：

- 只用于当前插件包的源码加密

优势：

- 每个插件包独立加密
- 不同包之间不共享实际内容密钥

### 密钥派生规则

建议：

```text
wrap_key = HKDF-SHA256(
  ikm = master_secret,
  salt = kid,
  info = "secspider:" + codeID + ":" + version
)
```

用途：

- `wrap_key` 用于包裹或解包 `content_key`

收益：

- 同一 `master_secret` 下，不同 `codeID/version` 的包不会直接共钥
- 支持按 `kid` 做宿主侧密钥轮换

## 密钥轮换策略

建议宿主维护一个 `keyring`，按 `kid` 管理签名公钥和主密钥材料。

设计要求：

- 插件头部必须携带 `kid`
- loader 先按 `kid` 查找密钥材料
- 找不到 `kid` 直接拒绝执行
- 新版插件可切换到新 `kid`
- 旧 `kid` 可在兼容期内继续保留

首版只需要支持静态内置 `keyring`，不要求联网拉取。

## 宿主加载设计

### 现状

当前宿主 `SpiderPluginLoader` 的核心流程为：

1. 安装兼容 `base.spider`
2. 通过本地路径或远程下载得到插件文件
3. 通过 `importlib.util.spec_from_file_location(...)` 执行源码文件
4. 从模块中读取 `Spider` 类并实例化

这条链路仅适合明文 Python 文件。

### 目标形态

宿主改造为双栈加载：

- 明文插件：保持现有 `importlib` 路径
- 加密插件：走自定义 `secspider` runtime 路径

两条路径最终都返回 `types.ModuleType`，上层实例化逻辑保持不变。

### 推荐改造点

在 `SpiderPluginLoader` 中新增三个私有方法：

- `_detect_package_format(source_path) -> str`
- `_load_plain_module(module_name, source_path) -> types.ModuleType`
- `_load_secspider_module(module_name, source_path, config) -> types.ModuleType`

主流程调整为：

1. `_install_compat_modules()`
2. `_resolve_source_path()`
3. `_detect_package_format(source_path)`
4. 如果不是 `secspider/1`，则走 `_load_plain_module(...)`
5. 如果是 `secspider/1`，则走 `_load_secspider_module(...)`
6. 统一读取 `Spider` 类、实例化并执行 `init(config.config_text)`

### 为什么不继续沿用 `spec_from_file_location`

原因如下：

- 密文插件正文不再是合法 Python 源码
- 若继续沿用 `importlib` 文件执行，势必要把明文源码先落盘
- 这会直接削弱“避免用户直接读取源码”的目标

因此，对加密插件的正确路径是：

- 把缓存文件当“文本包”
- 在内存中验签和解密
- 用 `compile/exec` 创建模块对象

## 宿主侧模块结构

建议新增如下模块：

- `atv_player/plugins/spider_crypto/package.py`
  - 解析 `secspider/1`
  - 校验头字段
  - 输出规范化签名输入
- `atv_player/plugins/spider_crypto/keyring.py`
  - 维护 `kid -> public_key/master_secret`
- `atv_player/plugins/spider_crypto/runtime.py`
  - 验签
  - 派生 `wrap_key`
  - 解包 `content_key`
  - 解密 `payload`
  - `compile/exec` 生成内存模块
- `atv_player/plugins/spider_crypto/errors.py`
  - 定义格式、签名、密钥、解密、运行期错误

`SpiderPluginLoader` 只负责调度，不直接承载加解密细节。

## 运行时序设计

密文插件的标准加载时序如下：

1. 读取插件文件文本
2. 解析注释头和 `payload.base64`
3. 检查 `format == secspider/1`
4. 按 `kid` 获取签名公钥
5. 对头字段和 payload 执行 `Ed25519` 验签
6. 验签通过后，按 `kid/codeID/version` 派生 `wrap_key`
7. 解开 `ek` 得到 `content_key`
8. 使用 `content_key + nonce` 解密 `payload`
9. 对解密后的源码做 `sha256` 校验，必须与 `hash` 一致
10. 将源码编译为 `code object`
11. 在新的 `types.ModuleType` namespace 中执行
12. 返回 module 对象给 `SpiderPluginLoader`

执行时应满足：

- 明文源码不写回磁盘
- 模块命名保持宿主当前风格
- 解密失败和运行失败分开报错

## 推荐的运行时接口

建议形成如下边界：

```python
class SecSpiderPackage:
    @classmethod
    def parse(cls, text: str) -> "SecSpiderPackage": ...
    def signing_bytes(self) -> bytes: ...

class SpiderKeyring:
    def get_public_key(self, kid: str): ...
    def get_master_secret(self, kid: str) -> bytes: ...

class SecSpiderRuntime:
    def __init__(self, keyring: SpiderKeyring) -> None: ...
    def load_module(self, pkg: SecSpiderPackage, module_name: str) -> types.ModuleType: ...
```

这样可以把：

- 包格式解析
- 密钥管理
- 运行时加载

三个责任分开，避免 `SpiderPluginLoader` 继续膨胀。

## 远程下载与缓存策略

当前宿主远程插件会下载后缓存到本地文件。此行为可以保留，但缓存内容应始终是“原始加密包文本”，而不是解密后的源码。

建议：

- `_resolve_source_path()` 继续负责下载并落地缓存
- 缓存文件只用于下次重新加载原始包
- 每次加载仍重新验签和解密
- 如需提速，只做内存级缓存，不做明文持久化缓存

缓存文件后缀可以考虑从固定 `.py` 调整为更中性的扩展名，例如：

- `.spkg`
- `.txt`

若短期不想改后缀，也应在代码语义上把其视为“插件文本缓存”，而不是默认假设为 Python 源码文件。

## 构建器设计

构建器职责如下：

1. 读取明文 Spider 源码
2. 计算源码 `sha256`
3. 生成随机 `content_key`
4. 生成随机 `nonce`
5. 可选压缩源码
6. 使用 `AES-256-GCM` 加密源码
7. 基于 `master_secret + kid + codeID + version` 派生 `wrap_key`
8. 用 `wrap_key` 包裹 `content_key`
9. 生成规范化包头
10. 对头部和 payload 做 `Ed25519` 签名
11. 输出最终文本封包

构建器只在受控环境中使用，不进入宿主。

## 错误分类设计

宿主侧应把底层异常统一映射为明确的用户可见错误：

- `插件格式不支持`
- `插件签名校验失败`
- `插件密钥不可用`
- `插件解密失败`
- `插件源码校验失败`
- `插件缺少 Spider 类`
- `插件运行失败: ...`
- `缺少依赖: ...`

这样做的目的是：

- 便于日志区分是下载问题、协议问题、签名问题还是运行问题
- 便于 UI 或调用方给出稳定提示

## 兼容与迁移策略

推荐分三步迁移：

### 第一步：宿主支持双栈

- 明文插件继续可加载
- 新增 `secspider/1` 加密插件加载能力

### 第二步：单插件试点

- 选择一个 Spider 先完成从明文到加密包的发布验证
- 检查下载、缓存、验签、解密和错误处理链路

### 第三步：逐步扩大覆盖面

- 将更多 Spider 改为由构建器生成加密包
- 明文源码只保留在私有开发或构建环境

本次设计不要求一次性淘汰全部明文插件。

## 测试策略

至少覆盖以下测试：

1. 包解析测试
   - 缺少字段
   - 重复字段
   - 非法 `format`
   - 缺失 `payload`
2. 验签测试
   - 改动头字段任一字符后验签失败
   - 改动 payload 任一字符后验签失败
3. 解密测试
   - 错误 `kid`
   - 错误 `ek`
   - 错误 `nonce`
   - 错误 `hash`
4. 模块加载测试
   - 成功加载后模块含 `Spider` 类
   - `init(config_text)` 能按现有方式调用
5. 兼容测试
   - 明文插件加载逻辑不回退
6. 缓存测试
   - 远程下载失败时，若已有有效缓存，仍能回退到缓存包

所有测试应使用本地 fixture，不依赖真实网络和真实私钥环境。

## 风险与约束

- 宿主主密钥可被逆向提取，因此无法防住高级对手
- 攻击者可以自行修改宿主，去掉验签和解密保护
- 若未来需要做授权控制，必须引入新的密钥分发或服务端参与机制
- 若协议字段顺序、空白或换行规则不固定，签名实现很容易出错，因此必须定义严格的 canonicalization 规则

## 验收标准

- 明文插件加载行为保持兼容
- `secspider/1` 插件可从本地和远程加载
- 被篡改的插件会在验签阶段拒绝执行
- 密钥错误或密文损坏会在解密阶段明确失败
- 加载成功后，宿主仍像处理普通插件一样处理 `Spider` 实例
- 解密后的源码不落盘
- 宿主错误提示可区分格式、签名、密钥、解密和运行期问题
