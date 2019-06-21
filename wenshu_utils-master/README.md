## 裁判文书相关解析/解密工具 for Python
截止到2019.06.01, 文书网现存的反爬参数基本都能在这找到  
全部参数解析/解密均用Python实现

Java示例请切换到java分支~

**此项目内容仅用于学习交流**

### 环境
1. python3.5+
2. 安装requirements.txt
3. nodejs(外部依赖)

默认是用python实现的方法去解析的，如果python出错了，就会调用nodejs去解析，所以还是要装nodejs

### 调用示例
参考demo.py 或 tests/里的测试用例 

### 测试
手动运行tests/里的测试用例

或

通过pytest测试
```bash
pip install pytest
pytest
```

或

通过docker构建测试
```bash
docker build -t wenshu_utils .  # 构建镜像
docker run --rm wenshu_utils    # 运行
```
