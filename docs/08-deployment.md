# 部署与运维

## 环境要求

- Python 3.9+
- 至少 2GB 可用内存（首次运行需下载 Embedding 模型）
- 可访问外网（抓取 RSS 和调用 LLM API）

## 安装步骤

### 1. 克隆或进入项目目录

```bash
cd C:\@richardcuick\aibes-news
```

### 2. 创建虚拟环境

```bash
python -m venv venv
```

### 3. 激活虚拟环境

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

首次运行会自动下载 `sentence-transformers` 模型到本地缓存。

### 5. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```env
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
SUMMARY_LANGUAGE=zh
MAX_CONTENT_TOKENS=3000
DATA_DIR=./data
```

`OPENAI_API_KEY` 为可选，不配置则使用降级摘要。

## 运行方式

### 单次运行

```bash
python main.py
```

### 带参数运行

```bash
# 不抓取正文
python main.py --no-body

# 不调用 LLM
python main.py --no-summary

# 自定义源配置
python main.py --feeds my-feeds.yaml
```

### 定时运行

#### 方式一：使用 scheduler.py

```bash
python scheduler.py --interval 4
```

每 4 小时运行一次。

#### 方式二：系统 Cron（推荐）

Linux/macOS：

```bash
crontab -e
```

添加：

```cron
0 */4 * * * cd /path/to/aibes-news && /path/to/venv/bin/python main.py >> /tmp/tech_intel.log 2>&1
```

#### 方式三：Windows 任务计划程序

1. 创建基本任务。
2. 触发器：每 4 小时一次。
3. 操作：启动程序 `python.exe`，参数 `main.py`，起始目录为项目路径。

## 启动 Web 看板

```bash
streamlit run app.py
```

访问 http://localhost:8501。

## 数据目录

```text
data/
├── news.db       # SQLite 数据库
├── chroma/       # Chroma 向量库
└── reports/      # Markdown 日报/周报
```

建议定期备份 `data/` 目录。

## 日志

当前日志输出到控制台，级别为 `INFO`。可通过修改各模块的 `logging.basicConfig` 调整。

后续可集成 `loguru` 或文件日志。

## 监控指标

| 指标 | 获取方式 |
|------|----------|
| 总收录数 | `storage.get_stats()["total"]` |
| 已向量化的记录数 | `storage.get_stats()["vectorized"]` |
| 每次新增数 | `main.py` 输出 |
| 报告文件 | `data/reports/` |

## 常见问题

### Q1: 安装依赖时报错

A: 确保 Python 版本 >= 3.9，并使用虚拟环境。Windows 上若安装 `lxml` 失败，可尝试：

```bash
pip install --upgrade pip
pip install lxml
```

### Q2: 某些 RSS 抓取失败

A: 可能是网络问题或源站限制。检查：

- 是否能直接访问该 RSS URL。
- 是否需要代理。
- 源的 `enabled` 是否设为 `false`。

### Q3: LLM 摘要为空或解析失败

A: 检查：

- `OPENAI_API_KEY` 是否正确。
- `OPENAI_BASE_URL` 是否可达。
- 模型是否支持 JSON 输出。

### Q4: 如何更新分类规则

A: 修改 `classifier.py` 中的 `CATEGORY_RULES` 和 `SOURCE_BIAS`，然后重新运行 `main.py`。

## 安全建议

- 不要将 `.env` 提交到 Git（已加入 `.gitignore`）。
- API Key 使用最小权限原则。
- 生产环境建议将 `DATA_DIR` 放在持久化卷上。
