# 上海图书馆开放数据 MCP —— 腾讯云开发(CloudBase)云托管 Dockerfile
# 参考官方模板: https://docs.cloudbase.net/ai/mcp/develop/host-mcp
# 原理: 本服务是 stdio MCP，容器内用 @cloudbase/mcp-transformer 把它转成 Streamable HTTP，
#       供远程客户端(Cursor/Claude/WorkBuddy 等)通过 https 访问。

FROM node:20-alpine

# 腾讯云 npm 镜像源（加速安装）
RUN npm config set registry https://mirrors.cloud.tencent.com/npm/ \
    && yarn config set registry https://mirrors.cloud.tencent.com/npm/

# Alpine 国内镜像源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tencent.com/g' /etc/apk/repositories

# 安装 Python 运行时（我们的 MCP 服务是纯标准库 Python，无需 pip 依赖）
RUN apk update \
    && apk add --no-cache python3 py3-pip curl

# 安装必须的转换工具：@cloudbase/mcp-transformer（官方固定版本）
RUN npm install -g @cloudbase/mcp-transformer@1.0.0-beta.18

# 拷贝服务代码（发布包内不含任何 APIKey）
COPY app/slc_mcp_server.py app/slc_endpoints.py /app/
WORKDIR /app

# 固定暴露端口
EXPOSE 80

# stdioToStreamable: 把 stdio MCP 转成远程 Streamable HTTP 服务
# --stdioCmd 指定启动命令（可用环境变量 $SLC_API_KEY，如需服务端统一使用某把 Key 可在云托管配置该环境变量；
#             发布版推荐不配置，让每个调用者通过 key 参数传自己的 Key）
CMD cloudbase-mcp-transformer stdioToStreamable --stdioCmd "python3 /app/slc_mcp_server.py" --port 80
