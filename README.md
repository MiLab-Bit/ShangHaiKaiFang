# 上海图书馆开放数据 MCP Server

> 第十一届上海图书馆开放数据竞赛 · 智能体作品的数据层
> 「典籍新生，数据里的文脉风华」

一个 **零 APIKey 硬编码**、纯 Python 标准库实现的 MCP（Model Context Protocol）服务器：
把上海图书馆开放数据平台的 **97 个 webapi 接口** + 搜韵诗词库（199 万首，免 token）封装成 12 个 MCP 工具，
可接入 WorkBuddy、Cursor、Claude Desktop、腾讯云开发 Agent 等任意 MCP 客户端，
并支持一键部署到 **腾讯云（Streamable HTTP）** 供公网调用。

---

## 特性

- 🧩 **12 个 MCP 工具**：覆盖家谱 / 古籍 / 碑帖 / 武康路 / 书目 / 地名志 / 红色事件 / 纪年表 / 电影 / 舆图 / 手迹 / 人名库等 97 个官方接口 + 搜韵诗词
- 🔑 **零 Key 硬编码**：代码内不存放任何竞赛 APIKey；Key 由每个使用者自行传入（工具参数 `key`），也可通过环境变量 `SLC_API_KEY` 注入
- 🐍 **零第三方依赖**：仅用 Python 标准库（urllib + json），`pip install` 都不需要
- ☁️ **可发布到腾讯云**：附 `slc_mcp_publish/` 发布包（Dockerfile + 上架配置 + 指南），stdio → Streamable HTTP 一键托管
- 🎵 **AIGC 歌词素材**：`souyun_poem` 免 token 检索 199 万首诗词（按作者/标题/诗句/朝代/体裁/韵部），`souyun_rhyme` / `souyun_couplet` 提供韵典和对仗词汇
- 📚 **RAG 骨架**：`rag_kb.py` 纯标准库 TF-IDF 知识库，可离线灌入官方 ZIP 数据

## 工具总览

| 工具 | 说明 | 需要 Key |
|---|---|---|
| `slc_endpoints` | 列出全部 97 个接口（id/家族/路径/参数），发现能力 | ❌ |
| `slc_api` | 通用分发器：调用任意 webapi 接口 | ✅ |
| `slc_era` | 中国历史纪年表：朝代/年号 ↔ 公元年（如 明 → 1368~1644） | ✅ |
| `slc_jiapu` | 家谱谱目检索 | ✅ |
| `slc_building` | 武康路历史建筑检索 | ✅ |
| `slc_red_event` | 红色旅游/历史事件检索 | ✅ |
| `slc_raw` | 任意 data1 路径 GET 兜底调用 | ✅ |
| `slc_datasets` / `slc_sparql` | 数据集总览 / SPARQL 说明 | ❌ |
| `souyun_poem` | 搜韵诗词检索（199 万首，免 token） | ❌ |
| `souyun_rhyme` | 韵典：查字所属韵部、词末/词首典故、句末诗例 | ❌ |
| `souyun_couplet` | 对仗词汇，写对仗句用 | ❌ |

> `slc_api` 覆盖的接口家族：近代城市文化(20)、古籍循证(15)、国漫革命文献(7)、武康路历史(7)、纪年表关联数据(5)、韬奋纪念馆(4)、书目数据(4)、家谱(4)、地名纪年(4)、竞赛PDF文献(3)、知识图谱人物(2)、文化总库机构(2)、舆图(2)、手迹(2)、红色旅游事件(2)、地名志(2)、纪年(2)、人名规范库(1)、机构名录(1)、其他(8)。

## 快速开始

### 方式一：本地 stdio 接入（推荐先这样体验）

```bash
# 1. 克隆仓库
git clone https://github.com/MiLab-Bit/ShangHaiKaiFang.git
cd ShangHaiKaiFang

# 2. 设置你的竞赛 APIKey（报名后官方邮件发放）
export SLC_API_KEY='你的上图书竞赛Key'    # macOS/Linux
# $env:SLC_API_KEY='你的上图书竞赛Key'    # Windows PowerShell

# 3. 运行端到端自测（免 Key 工具 + 需要 Key 工具）
python3 tests/test_stdio.py
```

在你的 MCP 客户端里配置 stdio 服务：

```json
{
  "mcpServers": {
    "上海图书馆开放数据": {
      "command": "python3",
      "args": ["/绝对路径/slc_mcp_server.py"],
      "env": { "SLC_API_KEY": "你的上图书竞赛Key" }
    }
  }
}
```

> WorkBuddy 用户可直接运行 `python3 setup_mcp_key.py --server 上海图书馆开放数据 --key 你的Key`
> 一键写入 `~/.workbuddy/mcp.json`（参考 `mcp.json.template`），然后在连接器管理页点「Trust」。

### 方式二：腾讯云发布（Streamable HTTP，公网可用）

1. 开通[云开发 CloudBase](https://tcb.cloud.tencent.com)（有免费额度），创建环境；
2. 云开发 AI+ 控制台创建**空白 MCP Server**（记下服务标识）；
3. 在 `slc_mcp_publish/` 目录执行：

```bash
npm i -g @cloudbase/cli@latest
tcb login
tcb cloudrun deploy    # 选择环境ID + 服务名
```

4. 服务详情页 `Tools` 标签验证 12 个工具；
5. 详情页 →「发布上架」→ 填写元信息并上传 `DOC.md` → 审核通过后出现在 [腾讯云 MCP 广场](https://cloud.tencent.com/developer/mcp)。

详细步骤、环境变量说明、排障表见 [`slc_mcp_publish/发布指南.md`](slc_mcp_publish/发布指南.md)。

## APIKey 说明（重要）

- 上海图书馆竞赛平台要求**每个调用者使用自己的竞赛 APIKey**（报名后官方邮件发放，仅限本届竞赛非商业使用）。
- 本仓库**不包含任何 Key**，也不记录、不收集你的 Key。
- Key 读取优先级：**工具参数 `key`** > 环境变量 `SLC_API_KEY`。
- 调用需要 Key 的工具时，把 Key 放在工具参数里：

```json
{ "endpoint": "building_list", "params": { "freetext": "武康路" }, "key": "你的上图书竞赛Key" }
```

- 免 Key 工具（`souyun_poem` / `souyun_rhyme` / `souyun_couplet` / `slc_endpoints`）开箱即用。
- ⚠️ 请勿把你的 Key 配置到公开服务的环境变量里（等于公开给所有调用者）。

## 目录结构

```
ShangHaiKaiFang/
├── README.md                 # 本文件
├── slc_mcp_server.py         # MCP 服务主程序（v1.3.0，纯标准库，零 Key）
├── slc_endpoints.py          # 97 个 webapi 接口注册表（自动生成）
├── gen_endpoints.py          # 接口注册表生成器（从官方 API 文档解析）
├── souyun_poem.py            # 搜韵诗词/韵典/对仗采集（AIGC 歌词素材，免 token）
├── rag_kb.py                 # RAG 知识库骨架（纯标准库 TF-IDF，可灌离线数据）
├── setup_mcp_key.py          # WorkBuddy 一键安装脚本（不含 Key）
├── mcp.json.template         # MCP 客户端配置模板（不含 Key）
├── slc_mcp_publish/          # 腾讯云发布包
│   ├── Dockerfile            #   CloudBase 云托管镜像（stdio → Streamable HTTP）
│   ├── mcp-meta.json         #   上架元信息
│   ├── DOC.md                #   上架接入文档
│   ├── 发布指南.md           #   6 步发布 + 排障
│   └── app/                  #   部署用服务代码
└── tests/                    # 测试（从环境变量读 Key，缺失会提示）
    ├── test_stdio.py         #   stdio 端到端（协议 + 真实调用）
    ├── test_live.py          #   handler 级实测（GET/POST/搜韵）
    └── test_mcp.py           #   协议冒烟测试
```

## 数据源与致谢

- **上海图书馆开放数据竞赛**：https://opendata.library.sh.cn/opendata/
- **搜韵诗词**：https://api.sou-yun.cn/open （199 万首诗词，免 token）
- 本仓库仅作竞赛/学习用途，接口版权归各数据方所有。

## License

[MIT](LICENSE)
