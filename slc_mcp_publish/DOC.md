# 上海图书馆开放数据 MCP Server

第十一届上海图书馆开放数据竞赛智能体作品的数据层。通过 MCP 协议把上海图书馆开放数据平台的 97 个 webapi 接口 + 搜韵诗词库暴露给任意 AI 客户端（Cursor / Claude / WorkBuddy / 云开发 Agent 等）。

## 能力

| 工具 | 说明 | 是否需要 Key |
|---|---|---|
| `slc_endpoints` | 列出全部 97 个接口（id/家族/路径/参数），发现能力 | 否 |
| `slc_api` | 通用分发器：调用任意一个 webapi 接口（家谱/古籍/碑帖/书目/舆图/手迹/地名志/武康路/红色事件/纪年表…） | 是 |
| `slc_era` | 中国历史纪年表：朝代/年号 ↔ 公元年 | 是 |
| `slc_jiapu` / `slc_building` / `slc_red_event` | 家谱谱目 / 武康路历史建筑 / 红色旅游事件 快捷查询 | 是 |
| `slc_raw` | 任意 data1 路径 GET 兜底 | 是 |
| `souyun_poem` | 搜韵诗词检索（按作者/标题/诗句/朝代/体裁/韵部），199万首 | 否 |
| `souyun_rhyme` / `souyun_couplet` | 韵典 / 对仗词汇，写诗填词、AIGC 歌词素材 | 否 |
| `slc_datasets` / `slc_sparql` | 数据集总览 / SPARQL 说明 | 否 |

## 快速开始（客户端接入）

在支持 MCP 的客户端中添加"Streamable HTTP"类型的服务，URL 填部署后得到的 `/messages` 地址（形如 `https://<服务域名>/messages`）。

### 免 Key 工具（开箱即用）
`slc_endpoints`、`souyun_poem`、`souyun_rhyme`、`souyun_couplet` 等无需任何凭证，连上即可使用。

### 需要 Key 的工具
上海图书馆竞赛平台要求每个调用者使用自己的竞赛 APIKey（报名后官方邮件发放）。调用时把 Key 放在工具参数 `key` 中即可：

```json
{ "endpoint": "building_list", "params": { "freetext": "武康路" }, "key": "你的上图书竞赛Key" }
```

服务端代码内不存放任何 Key，也不会记录你的 Key。

## 技术说明

- 纯 Python 标准库实现（urllib + json），零第三方依赖，零硬编码密钥。
- 数据源：`data1.library.sh.cn`（97 个 webapi，GET/POST 按官方文档区分）、`data.library.sh.cn`（纪年表）、`api.sou-yun.cn`（搜韵，免 token）。
- 部署形态：stdio → `@cloudbase/mcp-transformer` 转 Streamable HTTP → 腾讯云开发云托管。
