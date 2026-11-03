# 当前修改版完整架构

保留ChinaTravel原有LLMNeSy、沙盒检索、符号搜索与评估，加入四类软评分、20候选选优、修改后的prompt，以及最新C组的三餐、跨日和景点08:00–21:00硬检查。详见ARCHITECTURE.md；原项目说明与许可保留。

本次发布仅包含源码、配置样例、测试和10个固定输入案例；不含密钥、日志、缓存、中断现场、候选行程或HTML/JSON实验结果。官方数据通过scripts/bootstrap_data.py下载，版本和校验信息固定在data_sources.json。

从仓库根目录按README.md安装依赖、下载数据、配置.env.local，再运行experiments/c_only/prepare.py与driver.py。每例只跑一次，easy/human各5例；不会运行A/B/medium。每例最多30分钟、3路并行。prepare不调用模型，driver才开始付费请求。

当前仍存在已诊断的翻译和提前剪枝问题；上传的是现状完整架构，不代表这些问题已经修复。凌晨景点问题已增加搜索及最终审计两层硬检查。
