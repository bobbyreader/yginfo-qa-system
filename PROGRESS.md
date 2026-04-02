# YG智能知识库问答系统 - 部署进度

**更新时间**: 2026-04-02 15:16

## 项目状态: 待用户部署 ⚠️

代码已完成，Render 部署需要用户手动完成。

## 当前问题

**Site 返 404，`x-render-routing: no-server`**

- DNS 解析到 Render 成功
- 但没有任何活跃服务在运行
- **根因**：用户在 Render 上的部署未完成或服务被暂停

## 验证命令

```bash
# 返回 404 + x-render-routing: no-server → 服务不存在
curl -v https://yg-knowledge-base.onrender.com/health
```

## 已完成 ✅

1. ✅ 代码推送 GitHub (commit: fb20792)
2. ✅ `database.py` - URL 自动转换 `postgresql://` → `postgresql+asyncpg://`
3. ✅ `requirements.txt` - 包含 `asyncpg` 和 `psycopg[binary,pool]`
4. ✅ `render.yaml` - 部署配置完整

## 待用户操作（Owner 动作）

### 步骤一：登录 Render
1. 打开 https://render.com → 登录
2. 如果没有账号，用 GitHub 注册

### 步骤二：连接 GitHub 仓库
1. 点击 **New → Web Service**
2. 在 "Connect a GitHub repository" 搜索 `bobbyreader/yginfo-qa-system`
3. 点击 **Connect**

### 步骤三：配置环境变量
在 Render Web Service 设置页面，添加以下环境变量（**sync: false** 意味手动配置）：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DATABASE_URL` | Supabase PostgreSQL 连接串 | `postgresql://postgres.xxx:password@aws-0-xxx.pooler.supabase.com:6543/postgres` |
| `PINECONE_API_KEY` | Pinecone API Key | `pc-xxxxxx` |
| `OPENAI_API_KEY` | 中转 API Key | `sk-xxxxxx` |
| `OPENAI_BASE_URL` | 中转地址 | `https://api.minimax.chat/v1` |
| `PYTHON_VERSION` | Python 版本 | `3.12` |

### 步骤四：触发部署
1. 设置完成后，Render 会自动开始 Build
2. 或者手动点击 **Create Web Service** → 然后 **Manual Deploy → Deploy latest commit**

### 步骤五：验证
部署成功后：
```bash
curl https://yg-knowledge-base.onrender.com/health
# 应返回 {"status":"ok"}
```

## 部署架构

```
用户请求 → Render (FastAPI)
              ├── Supabase (PostgreSQL) - 存储文档、对话
              ├── Pinecone (向量数据库) - 存储 embedding
              └── 中转 API (MiniMax) - LLM 生成
```

## 代码仓库
https://github.com/bobbyreader/yginfo-qa-system

## 关键文件
- `backend/app/main.py` - FastAPI 入口，健康检查 `/health`
- `backend/app/core/config.py` - 配置
- `backend/app/core/database.py` - 数据库连接（已修复 asyncpg URL）
- `backend/app/services/` - 核心服务
- `render.yaml` - Render 部署配置
- `requirements.txt` - Python 依赖
