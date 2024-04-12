import json
import semantic_kernel as sk
from Plugins.utils import token_count
from Plugins.google_search import GoogleSearchPlugin
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

class SKReport:
    def __init__(self, report_title, lang):
        self.kernel = sk.Kernel()
        self.lang = lang
        self.api_key, _ = sk.openai_settings_from_dot_env()
        self.service_id = "default"
        self.kernel.add_service(
            OpenAIChatCompletion(service_id=self.service_id, 
                                 ai_model_id="gpt-3.5-turbo-0125", 
                                 api_key=self.api_key),
                                )

        self.plugin = self.kernel.import_plugin_from_prompt_directory("./Plugins/", "ReportPlugin")
        self.google_plugin = self.kernel.import_plugin_from_object(GoogleSearchPlugin(), plugin_name = "GoogleSearchPlugin")
        
        self.report_headings = []
        self.report_bodies = []
        self.report_tile = report_title
        self.TOKEN_LIMIT = 8000

        #importing functions from plugins
        self.OutlineJSON_function = self.plugin["OutlineJSON"]
        self.google_search_function = self.google_plugin["GoogleSearch"]
        self.get_content_function = self.google_plugin["GetContentFromURL"]

        self.column_function = self.plugin["Column"]
        self.query_function = self.plugin["Query"]
        self.Introduction_function = self.plugin["Introduction"]
        self.column_summ_function = self.plugin["ColumnSumm"]
        self.recommendation_function = self.plugin["Recommendation"]
        self.conclusion_function = self.plugin["Conclusion"]

        self.critics_function = self.plugin["Critics"]

    async def criticGenerator(self, prompt, input):
        return await self.kernel.invoke(self.critics_function, 
                                                sk.KernelArguments(
                                                    input = input,
                                                    prompt = prompt
                                                    )
                                                )
    
    async def outlineGenerator(self, critics = ""):
        while True: #Retry until format is correct
            try:
                self.OutlineJSON = await self.kernel.invoke(self.OutlineJSON_function, 
                                                       sk.KernelArguments(input=self.report_tile, lang = self.lang, critics = critics))
                self.json_split()
                break
            except:
                continue
    


    async def introGenerator(self, critics = ""):
        #write the introduction
        self.introContent = await self.kernel.invoke(self.Introduction_function, 
                                                sk.KernelArguments(
                                                    introduction=self.outline_intro,
                                                    reportLayout = self.outline_dict,
                                                    lang = self.lang,
                                                    critics = critics
                                                    )
                                                )

    async def columnist(self, heading:str, num_results:int=10, critics = ""):
        search_result = []
        tokens = 0

        query = str(await self.kernel.invoke(self.query_function, 
                                             sk.KernelArguments(
                                                 input = heading, 
                                                 big_title = self.outline_title,
                                                 lang = self.lang,
                                                 critics = ""
                                                 )
                                            )
                    )
        search_result_urls = await self.kernel.invoke(self.google_search_function, 
                                                      sk.KernelArguments(
                                                          keyword = query, 
                                                          num_results = num_results,
                                                          )
                                                    )
        search_result_urls = search_result_urls.value

        while True:
            if not search_result_urls:
                break
            url = search_result_urls.pop(0)
            content = await self.kernel.invoke(self.get_content_function, 
                                               sk.KernelArguments(
                                                   url = url
                                                   )
                                                )
            content = content.value
            new_tokens = token_count(content)
            if tokens + new_tokens > self.TOKEN_LIMIT:
                if tokens >= self.TOKEN_LIMIT//2:
                    break
                else:
                    continue
            tokens += new_tokens
            search_result.append(content)
        search_result = " ".join(search_result)
        column = await self.kernel.invoke(self.column_function, 
                                          sk.KernelArguments(
                                              input = search_result, 
                                              body_content = heading,
                                              lang = self.lang,
                                              critics = critics
                                              )
                                        )
        column_summ = await self.kernel.invoke(self.column_summ_function, 
                                               sk.KernelArguments(
                                                   input = search_result, 
                                                   body_content = heading,
                                                   lang = self.lang
                                                   )
                                                )
        
        return str(column), str(column_summ)

    async def recommendGenerator(self, summContent, critics = ""):
        self.recommendContent = str(await self.kernel.invoke(self.recommendation_function, 
                                                         sk.KernelArguments(
                                                             recommendation = self.outline_recommendations, 
                                                             summContent = summContent,
                                                             lang = self.lang,
                                                             critics = critics
                                                             )
                                                        )
                                    )
    
    async def conclusionGenerator(self, summContent, critics = ""):
        self.conclusionContent = str(await self.kernel.invoke(self.conclusion_function, 
                                                          sk.KernelArguments(
                                                            conclusion = self.outline_conclusion,
                                                            summContent = summContent,
                                                            lang = self.lang,
                                                            critics = critics
                                                            )
                                                        )
                                    )

    def json_split(self):
        if self.OutlineJSON:
            data = json.loads(str(self.OutlineJSON).replace("'", '"'))
            
            _data = {
                "title" : data['report']['title'],
                "introduction" : data['report']['introduction'],
                "body" : data['report']['body'],
                "conclusion" : data['report']['conclusion'],
                "recommendations" : data['report']['recommendations']
            }
            self.outline_dict = _data
            self.outline_title = _data['title']
            self.outline_intro = _data['introduction']
            self.outline_body = _data['body']
            self.outline_headings = _data['body']['headings']
            self.outline_conclusion = _data['conclusion']
            self.outline_recommendations = _data['recommendations']

            return _data
        else:
            return "Pls generate outline first!"