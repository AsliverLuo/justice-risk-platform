# NLP 能力验证报告

- 分类准确率（当前样本）：3/3 = 1.0
- 实体抽取平均覆盖率：0.5333
- 法条关联平均命中率：0.6667

## 崔某劳务合同纠纷二审民事判决书
- 分类：labor_service_dispute（期望：labor_service_dispute，mode=openai）
- 实体抽取 mode：openai，overall=0.4
  - persons: score=1.0，expected=['崔某', '张某']，predicted=['崔某', '张某']
  - companies: score=1.0，expected=['北京某公司']，predicted=['北京某公司', '北京某学院']
  - amounts: score=0.0，expected=['23127元']，predicted=['23127 元']
  - dates: score=0.0，expected=['2025年1月20日']，predicted=['2025 年 1 月 20 日']
  - addresses: score=0.0，expected=['北京市昌平区']，predicted=['北京某学院某路及图书馆西']
- 法条关联 mode：openai，score=0.0，matched=[]
- 法条候选数：12

## 某公司;张某;魏某劳务合同纠纷二审民事判决书
- 分类：labor_service_dispute（期望：labor_service_dispute，mode=openai）
- 实体抽取 mode：openai，overall=0.6
  - persons: score=1.0，expected=['魏某', '张某']，predicted=['张某', '魏某']
  - companies: score=1.0，expected=['某公司']，predicted=['某公司', '某学院']
  - amounts: score=0.0，expected=['5280元']，predicted=['5280 元']
  - dates: score=0.0，expected=['2025年1月20日']，predicted=['2025 年 1 月 20 日']
  - addresses: score=1.0，expected=[]，predicted=['某地']
- 法条关联 mode：openai，score=1.0，matched=['保障农民工工资支付条例|第三十六条']
- 法条候选数：12

## 张某云与张某森离婚纠纷支持起诉案——检例第126号
- 分类：other（期望：other，mode=openai）
- 实体抽取 mode：openai，overall=0.6
  - persons: score=1.0，expected=['张某云', '张某森']，predicted=['张某云', '张某森']
  - companies: score=1.0，expected=[]，predicted=['河北省武邑县人民检察院', '武邑县检察院', '武邑县法院', '衡水市中级人民法院']
  - amounts: score=1.0，expected=[]，predicted=[]
  - dates: score=0.0，expected=['2020年4月12日', '2020年5月28日', '2020年7月15日']，predicted=['2020 年 4 月 12 日', '2020 年 5 月 28 日', '2020 年 7 月 15 日']
  - addresses: score=0.0，expected=['河北省武邑县人民检察院']，predicted=[]
- 法条关联 mode：openai，score=1.0，matched=['中华人民共和国民事诉讼法|第十五条']
- 法条候选数：12
