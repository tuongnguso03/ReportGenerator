from googlesearch import search
from newspaper import Article
import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function

class GoogleSearchPlugin:
    """
    Provides functions to make google search
    """
    @kernel_function(name="GoogleSearch")
    def search_google(self, 
            keyword: Annotated[str, "The search query"], 
            num_results: Annotated[int, "The number of result needed"]
        ) -> Annotated[list[str], "The output is a list of urls"]:
        """Returns the list of urls that is related to the query."""
        try:
            search_results = search(keyword, num=num_results, stop=num_results)
            return search_results
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return
    
    @kernel_function(name = "GetContentFromURL")
    def get_content(self,
            url: Annotated[str, "The web url"], 
        ) -> Annotated[str, "The content of the url"]:
        """Returns the content of the article from the given url"""
        article = Article(url)
        for i in range(10):
            try:
                article.download() #try to download until the end
                article.parse()
                break
            except:
                continue
        return article.text
