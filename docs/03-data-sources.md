# 数据源分析

## 源分类体系

根据技术情报覆盖范围，将数据源划分为 6 大类：

```text
1. 官方源        → 头部 AI/科技公司官方发布
2. 研究源        → 学术论文与基础研究
3. 工程源        → 开发者社区与工程实践
4. 云厂商源      → 云计算与 AI 基础设施
5. 安全与开源     → 安全公告与开源生态
6. 中文源        → 中文技术媒体
```

## 1. 官方源

**定位**：获取 AI 与科技巨头的产品发布、研究进展、安全动态等一手信息。

| 源 | URL | 特点 |
|----|-----|------|
| OpenAI News | https://openai.com/news/rss.xml | 产品、研究、安全 |
| Anthropic News | https://www.anthropic.com/news/rss.xml | Claude、AI 安全 |
| Google AI Blog | https://ai.googleblog.com/feeds/posts/default | 研究与应用 |
| Microsoft Research | https://www.microsoft.com/en-us/research/feed/ | 研究与工程 |
| Meta AI Blog | https://ai.meta.com/blog/rss/ | 模型、研究 |
| NVIDIA Blog | https://blogs.nvidia.com/blog/feed/ | 芯片、AI 基础设施 |
| GitHub Blog | https://github.blog/feed/ | 开发者产品、安全 |

**默认加权**：`公司动态/投融资 +30%`，`AI/LLM +20%`。

## 2. 研究源

**定位**：追踪 AI/ML/NLP/CV 领域的最新论文。

| 源 | URL | 特点 |
|----|-----|------|
| arXiv cs.AI | https://rss.arxiv.org/rss/cs.AI | 人工智能 |
| arXiv cs.LG | https://rss.arxiv.org/rss/cs.LG | 机器学习 |
| arXiv cs.CL | https://rss.arxiv.org/rss/cs.CL | 计算语言学 |
| arXiv cs.CV | https://rss.arxiv.org/rss/cs.CV | 计算机视觉 |

**默认加权**：`研究 +50%`，`AI/LLM +20%`。

## 3. 工程源

**定位**：开发者社区、工程实践、技术趋势。

| 源 | URL | 特点 |
|----|-----|------|
| Hacker News Frontpage | https://hnrss.org/frontpage | 技术热点讨论 |
| Lobsters | https://lobste.rs/rss | 开发者社区 |
| InfoQ | https://feed.infoq.com/ | 企业技术 |
| The New Stack | https://thenewstack.io/feed/ | 云原生、DevOps |
| Stack Overflow Blog | https://stackoverflow.blog/feed/ | 开发者生态 |

**默认加权**：`编程/工程 +50%`，`开源 +20%`。

## 4. 云厂商源

**定位**：云计算、AI 平台、基础设施服务动态。

| 源 | URL | 特点 |
|----|-----|------|
| AWS Machine Learning Blog | https://aws.amazon.com/blogs/machine-learning/feed/ | AWS AI 服务 |
| Google Cloud Blog | https://cloudblog.withgoogle.com/feeds/posts/default?alt=rss | GCP 动态 |
| Azure AI Blog | https://azure.microsoft.com/en-us/blog/topics/ai/feed/ | Azure AI |
| Cloudflare Blog | https://blog.cloudflare.com/rss/ | 网络与安全 |

**默认加权**：`云原生 +80%`，`AI/LLM +10%`。

## 5. 安全与开源

**定位**：安全漏洞、攻击事件、开源基金会动态。

| 源 | URL | 特点 |
|----|-----|------|
| CISA Alerts | https://www.cisa.gov/news.xml | 安全公告 |
| GitHub Security | https://github.blog/category/security/feed/ | 供应链安全 |
| Krebs on Security | https://krebsonsecurity.com/feed/ | 安全调查 |
| The Hacker News | https://feeds.feedburner.com/TheHackersNews | 安全新闻 |
| Linux Foundation | https://www.linuxfoundation.org/blog/feed/ | 开源生态 |

**默认加权**：`安全 +80%`，`开源 +30%`。

## 6. 中文源

**定位**：中文技术媒体对 AI、开源、行业的报道与解读。

| 源 | URL | 特点 |
|----|-----|------|
| 机器之心 | https://www.jiqizhixin.com/rss | AI 资讯 |
| 量子位 | https://www.qbitai.com/feed | AI/科技 |
| InfoQ中文 | https://www.infoq.cn/feed | 企业技术 |
| AI科技评论 | https://www.leiphone.com/feed | AI 深度 |
| 开源中国 | https://www.oschina.net/news/rss | 开源 |
| 掘金 | https://juejin.cn/rss | 开发者 |

**默认加权**：`AI/LLM +20%`，`行业应用 +20%`。

## 源配置格式

每个源在 `feeds.yaml` 中统一配置：

```yaml
category_key:
  name: 显示名称
  sources:
    - name: 源名称
      url: RSS 地址
      type: rss
      enabled: true
      max_items: 15
```

## 源管理与扩展

- 新增源：在对应分组下添加即可。
- 禁用源：设置 `enabled: false`。
- 控制数量：调整 `max_items`。
- 后续可扩展 `type: api` 或 `type: html` 以支持非 RSS 源。
