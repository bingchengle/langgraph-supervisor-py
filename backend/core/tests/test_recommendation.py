from simple_app import analyze_user_need

# 测试适合新手的微调项目
result = analyze_user_need('适合新手的微调项目')

print('\n推荐结果:')
for i, project in enumerate(result['projects'], 1):
    print(f'{i}. {project["name"]} - {project["description"]}')

# 测试适合新手的RAG项目
print('\n\n测试适合新手的RAG项目:')
result2 = analyze_user_need('适合新手的RAG项目')

print('\n推荐结果:')
for i, project in enumerate(result2['projects'], 1):
    print(f'{i}. {project["name"]} - {project["description"]}')
