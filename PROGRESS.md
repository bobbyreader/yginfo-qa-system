# YG智能知识库问答系统 - 工作进度

**最后更新**: 2026-04-02 17:30

## 项目状态: 部署中（数据库连接卡住）🔄

## 已完成的修复

### 代码层面 ✅
1. ✅ `requirements.txt` - 添加 `rank-bm25==0.2.2`
2. ✅ `requirements.txt` - 添加 `python-multipart==0.0.12`
3. ✅ `requirements.txt` - 添加 `pypdf==5.1.0`
4. ✅ `requirements.txt` - 添加 `python-docx==1.1.2`
5. ✅ `database.py` - URL 自动转换 `postgresql://` → `postgresql+asyncpg://`
6. ✅ `intent.py` - LLM 调用加 try-except + hasattr 兼容中转API
7. ✅ `generation.py` - LLM 调用加 try-except 异常处理
8. ✅ `chat.py` - _generate_recommendations 加异常处理
9. ✅ `embedding.py` - 改用 httpx 直接调用中转API（不用SDK）
10. ✅ `retrieval.py` - hybrid_search 加降级逻辑

### 部署层面 ⚠️
- ✅ Site 访问正常：https://yginfo-qa-system-1.onrender.com
- ✅ /health 200
- ✅ /docs 200
- ❌ /api/chat/message 500 — 数据库连接问题

## 当前卡点：Supabase 数据库连接

### 问题演进
1. 最初：DNS 解析失败（主机名错误）
2. 然后：Tenant or user not found（Pooler 地址，密码或用户名问题）
3. 最后：Network unreachable（直接连接 5432 被 Render 网络封锁）

### 根因
- Render 免费版无法直连 Supabase 5432 端口（被封锁）
- 必须使用 Supabase Pooler（端口 6543）
- Pooler 连接报错 "Tenant or user not found" = 连接串格式问题

### 下一步操作
1. 登录 Supabase Dashboard → Settings → Database
2. 找到 **Connection Pooling** 部分
3. 复制 **pooler.supabase.com** 的连接串（不是 direct）
4. 密码中的 `@` 需要 URL 编码为 `%40`
5. 在 Render 上更新 `DATABASE_URL` 环境变量
6. 重新 Deploy

### 预期正确的连接串格式
```
postgresql://postgres:002063%40YGSOFT@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

注意：
- 端口是 **6543**（不是 5432）
- 密码 `002063@YGSOFT` → `002063%40YGSOFT`

## Git 提交记录
- `f441175` - fix: add missing rank-bm25 dependency
- `405f688` - fix: add missing dependencies - python-multipart, pypdf, python-docx
- `4554aa1` - fix: handle non-standard LLM responses from proxy APIs
- `2e0a87e` - fix: replace OpenAI SDK embedding with direct httpx calls

## 部署地址
https://yginfo-qa-system-1.onrender.com/docs
