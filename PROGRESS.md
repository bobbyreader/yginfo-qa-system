# YG智能知识库问答系统 - 部署进度

**更新时间**: 2026-04-02 14:20

## 项目状态: 部署中 🔄

代码已完成，Render 部署遇到问题正在修复中。

## 当前问题

**Build 成功，Runtime 失败**：
- 错误：`ModuleNotFoundError: No module named 'psycopg2'`
- 原因：Supabase 给的连接串是 `postgresql://`，但 SQLAlchemy 异步需要 `postgresql+asyncpg://`

## 已修复

✅ `database.py` - 添加 URL 自动转换 `postgresql://` → `postgresql+asyncpg://`
✅ 已推送到 GitHub (commit: fb20792)

## 待完成

- [ ] 在 Render 重新部署 (Manual Deploy → Deploy latest commit)
- [ ] 验证服务启动成功
- [ ] 测试 API 接口

## 部署架构

```
用户请求 → Render (FastAPI)
              ├── Supabase (PostgreSQL) - 存储文档、对话
              ├── Pinecone (向量数据库) - 存储 embedding
              └── 中转 API (MiniMax) - LLM 生成
```

## 环境变量 (已在 Render 配置)

| 变量名 | 值 |
|--------|-----|
| `DATABASE_URL` | Supabase PostgreSQL 连接串 |
| `PINECONE_API_KEY` | Pinecone API Key |
| `OPENAI_API_KEY` | 中转 API Key |
| `OPENAI_BASE_URL` | 中转地址 |
| `PYTHON_VERSION` | `3.12.10` |

## 快速恢复

1. 打开 Render Dashboard → yg-knowledge-base 服务
2. 点击 Manual Deploy → Deploy latest commit
3. 等待部署完成，查看 Logs 确认无错误
4. 访问 https://yg-knowledge-base.onrender.com/docs 查看 API 文档

## 代码仓库
https://github.com/bobbyreader/yginfo-qa-system

## 关键文件
- `backend/app/main.py` - FastAPI 入口
- `backend/app/core/config.py` - 配置（支持 openai_base_url 中转）
- `backend/app/core/database.py` - 数据库连接（已修复 asyncpg URL）
- `backend/app/services/` - 核心服务 (retrieval, generation, embedding, intent)
- `render.yaml` - Render 部署配置
- `PROGRESS.md` - 本文件
