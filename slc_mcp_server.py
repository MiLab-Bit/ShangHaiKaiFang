#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上海图书馆开放数据 MCP 服务（手写 stdio 协议，零第三方依赖）
工具清单：
  数据平台（data1.library.sh.cn，需 SLC_API_KEY）：
    slc_era / slc_jiapu / slc_building / slc_red_event
    slc_api          【通用分发器】调用 api_2025 注册的 97 个 webapi 接口
    slc_endpoints    列出全部可用接口（发现能力）
    slc_datasets / slc_sparql / slc_raw
  搜韵诗词（api.sou-yun.cn/open，免 token，服务 AIGC 歌曲）：
    souyun_poem / souyun_rhyme / souyun_couplet
依赖：仅标准库。Key 获取优先级：调用参数 key > 环境变量 SLC_API_KEY（mcp.json 的 env）。
发布版（腾讯云云托管/公网）代码内不含任何 Key，每个调用者传自己的 key 参数。
"""
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error

try:
    from slc_endpoints import ENDPOINTS
except Exception:
    ENDPOINTS = []

BASE = "https://data1.library.sh.cn"
SOUYUN = "https://api.sou-yun.cn/open"
KEY = os.environ.get("SLC_API_KEY", "")


def _resolve_key(a):
    """key 优先级：调用参数 key > 环境变量 SLC_API_KEY（发布版代码内不存放任何 Key）。"""
    return (a.get("key") or "").strip() or KEY


def _no_key():
    return json.dumps({"status": 400, "error": "缺少 APIKey：请传入 key 参数（每个使用者填自己的上图书竞赛 Key，勿使用他人 Key）"}, ensure_ascii=False)


def _http_req(method, url, data=None, headers=None):
    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "ignore")[:800]
        except Exception:
            body = ""
        return e.code, body
    except Exception as e:
        return 0, repr(e)


def _http_get(url, accept="application/json"):
    return _http_req("GET", url, headers={"Accept": accept})


def slc_call(endpoint_id, params=None, path_args=None, key=None):
    params = params or {}
    path_args = path_args or []
    ep = next((e for e in ENDPOINTS if e["id"] == endpoint_id), None)
    if not ep:
        return 404, json.dumps({"error": "未知 endpoint", "hint": "用 slc_endpoints 查看可用 id"})
    try:
        path = ep["path"].format(*path_args) if path_args else ep["path"]
    except Exception as e:
        return 400, json.dumps({"error": "path_args 不足", "need": ep["path_params"], "detail": str(e)}, ensure_ascii=False)
    # ep["path"] 已是完整 URL（含 host），不要再拼 BASE；相对路径才拼
    base_url = path if path.startswith("http") else BASE + path
    method = ep.get("method", "GET").upper()
    q = dict(params)
    if ep.get("needs_key"):
        k = key or KEY
        if not k:
            return 400, _no_key()
        q["key"] = k
    if method == "POST":
        # POST 接口：查询参数走 JSON body；key 仍按文档放在 query 上
        body = json.dumps(params, ensure_ascii=False).encode("utf-8")
        post_url = base_url
        if ep.get("needs_key"):
            post_url += "?" + urllib.parse.urlencode({"key": key or KEY})
        return _http_req("POST", post_url, data=body,
                         headers={"Content-Type": "application/json"})
    url = base_url + "?" + urllib.parse.urlencode(q)
    return _http_req("GET", url)


def _wrap(status, text):
    try:
        return json.dumps({"status": status, "data": json.loads(text)}, ensure_ascii=False)
    except Exception:
        return json.dumps({"status": status, "text": text[:2000]}, ensure_ascii=False)


# ---------------- 工具实现 ----------------
def t_era(a):
    term = a.get("term", "")
    k = _resolve_key(a)
    if not k:
        return _no_key()
    url = BASE + "/data/" + urllib.parse.quote(term) + "?key=" + k
    s, t = _http_get(url)
    return _wrap(s, t)


def t_jiapu(a):
    k = _resolve_key(a)
    s, t = slc_call("work_data", {"title": a.get("title", ""), "familyname": a.get("familyname", "")}, key=k)
    return _wrap(s, t)


def t_building(a):
    k = _resolve_key(a)
    s, t = slc_call("building_list", {"freetext": a.get("keyword", "")}, key=k)
    return _wrap(s, t)


def t_red_event(a):
    kw = a.get("keyword", "")
    p = {"eventFreeText": kw} if kw else {"eventDate": a.get("date", "")}
    s, t = slc_call("route_getEventList", p, key=_resolve_key(a))
    return _wrap(s, t)


def t_api(a):
    eid = a.get("endpoint", "")
    if not any(e["id"] == eid for e in ENDPOINTS):
        fam = [e for e in ENDPOINTS if e.get("family") == eid]
        if fam:
            eid = fam[0]["id"]
        else:
            return json.dumps({"error": "endpoint 未找到", "hint": "用 slc_endpoints 查看可用 id"}, ensure_ascii=False)
    params = a.get("params") or {}
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except Exception:
            params = {}
    path_args = a.get("path_args") or []
    s, t = slc_call(eid, params, path_args, key=_resolve_key(a))
    return _wrap(s, t)


def t_endpoints(a):
    fam = a.get("family", "")
    items = [{"id": e["id"], "family": e["family"], "path": e["path"],
              "params": e["params"], "path_params": e["path_params"]}
             for e in ENDPOINTS if (not fam or e["family"] == fam)]
    return json.dumps({"count": len(items), "endpoints": items}, ensure_ascii=False)


def t_datasets(a):
    return json.dumps(DATASETS, ensure_ascii=False)


def t_sparql(a):
    note = ("本届竞赛 Key 的 SPARQL JSON 结果被服务端拦截，仅网页端 https://data.library.sh.cn/sparql 可用。"
            "如需图查询，请在网页端验证语句后，用 slc_raw 调用其它 REST/webapi 接口。")
    return json.dumps({"status": "blocked", "note": note}, ensure_ascii=False)


def t_raw(a):
    path = a.get("path", "")
    params = a.get("params") or {}
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except Exception:
            params = {}
    k = _resolve_key(a)
    if not k:
        return _no_key()
    q = dict(params)
    q["key"] = k
    url = BASE + path + "?" + urllib.parse.urlencode(q)
    s, t = _http_get(url)
    return _wrap(s, t)


def t_poem(a):
    p = {"key": a.get("keyword", ""), "jsontype": "true"}
    for k in ("scope", "dynasty", "type", "rhyme"):
        if a.get(k):
            p[k] = a[k]
    if a.get("pageno"):
        p["pageno"] = a["pageno"]
    s, t = _http_get(SOUYUN + "/poem?" + urllib.parse.urlencode(p))
    return _wrap(s, t)


def t_rhyme(a):
    p = {"id": a.get("char", "")}
    if a.get("qtype") is not None:
        p["qtype"] = a["qtype"]
    s, t = _http_get(SOUYUN + "/rhymeDictionary?" + urllib.parse.urlencode(p))
    return _wrap(s, t)


def t_couplet(a):
    s, t = _http_get(SOUYUN + "/coupletwords?" + urllib.parse.urlencode({"id": a.get("word", "")}))
    return _wrap(s, t)


DATASETS = {
    "本届主题": "典籍新生，数据里的文脉风华",
    "赛道": ["应用开发及智能体", "创意论文", "AIGC应用(微电影/歌曲/海报)"],
    "核心平台(需Key)": {
        "纪年/关联数据/SPARQL/内容协商": "data.library.sh.cn",
        "分类型 webapi(97个)": "data1.library.sh.cn，见 slc_endpoints",
    },
    "第三方机构(部分)": {
        "搜韵诗词(199万首/对仗300万)": "api.sou-yun.cn/open，免token，见 souyun_* 工具",
        "上海韬奋纪念馆": "zoutaofen 系列",
        "Artlib世界艺术鉴赏库": "17万幅美术图(需独立Key)",
        "CBDB中国历代人物传记": "64.9万人(离线ZIP)",
        "全国报刊索引": "晚清/民国期刊(需独立Key)",
    },
    "离线包": "上海图书馆开放数据2026.zip（含 API 文档/使用数据；大文化库走 API）",
}


def S(name, desc, props, required=None):
    """构造一个工具描述，避免手写嵌套括号出错。"""
    sch = {"type": "object", "properties": props}
    if required:
        sch["required"] = required
    return {"name": name, "description": desc, "inputSchema": sch}


TOOLS = [
    S("slc_era", "中国历史纪年表：输入朝代/年号返回公元年范围，或反之。例：明 -> 1368~1644。发布版请传 key（自己的上图书竞赛Key）。",
      {"term": {"type": "string", "description": "朝代/年号/公元年，如 明、洪武、1369"},
       "key": {"type": "string", "description": "上图书竞赛 APIKey（发布版必填，每个使用者填自己的）"}}, ["term"]),
    S("slc_jiapu", "家谱谱目检索（data1）。可按谱名/姓氏检索",
      {"title": {"type": "string"}, "familyname": {"type": "string"},
       "key": {"type": "string", "description": "上图书竞赛 APIKey（发布版必填）"}}),
    S("slc_building", "武康路历史建筑检索（已验证可用）",
      {"keyword": {"type": "string", "description": "路名/建筑关键词，如 武康路"},
       "key": {"type": "string", "description": "上图书竞赛 APIKey（发布版必填）"}}, ["keyword"]),
    S("slc_red_event", "红色旅游/历史事件检索",
      {"keyword": {"type": "string"}, "date": {"type": "string", "description": "年份，如 1940"},
       "key": {"type": "string", "description": "上图书竞赛 APIKey（发布版必填）"}}),
    S("slc_api", "通用分发器：调用 api_2025 注册的全部 webapi 接口（家谱/古籍/盛档/人名库/碑帖/电影/期刊/舆图/书目/地名志/武康路 等 97 个）。endpoint 填接口 id；params 填查询参数(JSON)；path_args 填路径占位{0}{1}；key 填自己的上图书竞赛Key（发布版必填）。先用 slc_endpoints 查 id。",
      {"endpoint": {"type": "string", "description": "接口 id 或 家族名(取该家族首个接口)"},
       "params": {"type": "object", "description": "查询参数，如 freetext=江南, pageNum=1"},
       "path_args": {"type": "array", "items": {"type": "string"}, "description": "路径占位 {0}{1} 的取值列表"},
       "key": {"type": "string", "description": "上图书竞赛 APIKey（发布版必填）"}}, ["endpoint"]),
    S("slc_endpoints", "列出全部可用 webapi 接口（id/家族/路径/参数），可按 family 过滤。用于发现能力。",
      {"family": {"type": "string", "description": "可选：按家族过滤，如 古籍循证 / 武康路历史"}}),
    S("slc_datasets", "数据集与第三方机构总览", {}),
    S("slc_sparql", "SPARQL 图查询说明（本届 Key 仅网页端可用）", {}),
    S("slc_raw", "任意 data1.library.sh.cn 路径的 GET 兜底调用",
      {"path": {"type": "string", "description": "路径，如 /webapi/beitie/search"},
       "params": {"type": "object"},
       "key": {"type": "string", "description": "上图书竞赛 APIKey（发布版必填）"}}, ["path"]),
    S("souyun_poem", "搜韵诗词检索（免token）：按作者/标题/诗句/朝代/体裁/韵部查诗词，服务 AIGC 歌词。",
      {"keyword": {"type": "string", "description": "关键词或诗ID，如 王之涣 / 登鹳雀楼 / 7734"},
       "scope": {"type": "string", "description": "All/Author/Title/Sentence"},
       "dynasty": {"type": "string", "description": "如 Tang/Song"},
       "type": {"type": "string", "description": "体裁，如 QiLv/WuJue"},
       "rhyme": {"type": "string", "description": "韵部，如 江/尤"},
       "pageno": {"type": "integer"}}, ["keyword"]),
    S("souyun_rhyme", "搜韵韵典：查字所属韵部、词末/词首典故、句末诗例（免token）",
      {"char": {"type": "string", "description": "韵字，如 天/月"},
       "qtype": {"type": "integer", "description": "0全部 1韵目 2词末典故 3词首 4词末 5句末诗例"}}, ["char"]),
    S("souyun_couplet", "搜韵对仗词汇：返回与输入字/词对仗的词汇（免token），写对仗句用",
      {"word": {"type": "string", "description": "字或词，如 人间/月"}}, ["word"]),
]

HANDLERS = {
    "slc_era": t_era, "slc_jiapu": t_jiapu, "slc_building": t_building,
    "slc_red_event": t_red_event, "slc_api": t_api, "slc_endpoints": t_endpoints,
    "slc_datasets": t_datasets, "slc_sparql": t_sparql, "slc_raw": t_raw,
    "souyun_poem": t_poem, "souyun_rhyme": t_rhyme, "souyun_couplet": t_couplet,
}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        rid = req.get("id")
        method = req.get("method")
        if method == "initialize":
            resp = {"jsonrpc": "2.0", "id": rid, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "shanghai-library-opendata", "version": "1.3.0"}}}
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            name = req.get("params", {}).get("name", "")
            args = req.get("params", {}).get("arguments", {})
            handler = HANDLERS.get(name)
            if handler:
                try:
                    out = handler(args)
                except Exception as e:
                    out = json.dumps({"error": str(e)}, ensure_ascii=False)
            else:
                out = json.dumps({"error": "unknown tool"}, ensure_ascii=False)
            resp = {"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text", "text": out}]}}
        else:
            resp = {"jsonrpc": "2.0", "id": rid, "result": {}}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
