# YG智能知识库问答系统

多渠道接入的企业级智能客服系统，基于知识库文档提供多轮对话和主动推荐能力。

## 功能特性

- 多渠道接入: 支持网页Widget、企业微信等多渠道
- 知识库管理: 支持PDF、Word文档上传与解析
- 智能检索: RAG Pipeline + 混合检索（向量+BM25）
- 多轮对话: 支持上下文理解和对话历史
- 主动推荐: 基于用户问题推荐相关问题

## 快速开始

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # 配置API密钥
uvicorn app.main:app --reload --port 8000
```

## 项目结构

```
backend/
├── app/
│   ├── api/          # API路由
│   ├── core/         # 配置、数据库
│   ├── models/       # 数据模型
│   └── services/      # 业务逻辑
frontend/
├── widget/           # 网页Widget
└── admin/           # 管理后台
```

## API接口

- POST /api/chat/message - 对话
- POST /api/knowledge/documents/upload - 上传文档
- GET /api/admin/documents - 管理文档

## 许可证

MIT
