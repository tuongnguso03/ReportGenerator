from typing import Dict
import streamlit as st
import asyncio
import roman
import os
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from Plugins.utils import json_split, token_count, create_docx
from Plugins.google_search import GoogleSearchPlugin


TOKEN_LIMIT = 8000

async def columnist(heading, title, google_search_function, get_content_function, column_function, column_summ_function, query_function):
    search_result = []
    tokens = 0

    query = str(await kernel.invoke(query_function, sk.KernelArguments(input = heading, big_title = title)))
    search_result_urls = await kernel.invoke(google_search_function, sk.KernelArguments(keyword = query, num_results = 15))
    search_result_urls = search_result_urls.value
    while True:
        if not search_result_urls:
            break
        url = search_result_urls.pop(0)
        content = await kernel.invoke(get_content_function, sk.KernelArguments(url = url))
        content = content.value
        new_tokens = token_count(content)
        if tokens + new_tokens > TOKEN_LIMIT:
            if tokens >= TOKEN_LIMIT//2:
                break
            else:
                continue
        tokens += new_tokens
        search_result.append(content)
    search_result = " ".join(search_result)
    column = await kernel.invoke(column_function, sk.KernelArguments(input = search_result, body_content = heading))
    column_summ = await kernel.invoke(column_summ_function, sk.KernelArguments(input = search_result, body_content = heading))

    with st.chat_message("Assistant"):
        st.markdown("## " + heading + "\n" + str(column) +"\n")
    return str(column), str(column_summ)

async def generate_report(title, kernel, plugin, google_plugin):

    with st.chat_message("Assistant"):
        st.markdown("# "+ title)

    column_headings = []
    column_bodies = []
    #importing functions from plugins
    OutlineJSON_function = plugin["OutlineJSON"]
    google_search_function = google_plugin["GoogleSearch"]
    get_content_function = google_plugin["GetContentFromURL"]

    column_function = plugin["Column"]
    query_function = plugin["Query"]
    Introduction_function = plugin["Introduction"]
    column_summ_function = plugin["ColumnSumm"]

    #Get JSON outline
    while True: #Retry until format is correct
        try:
            OutlineJSON = await kernel.invoke(OutlineJSON_function, sk.KernelArguments(input=title))
            outline_dict = json_split(str(OutlineJSON))
            break
        except:
            continue
    #write the introduction
    Introduction = await kernel.invoke(Introduction_function, sk.KernelArguments(introduction=outline_dict["introduction"]
                                                                            , reportLayout = str(OutlineJSON)))
    introduction = "## " +roman.toRoman(1) + f". Mở Đầu \n {str(Introduction)}"

    with st.chat_message("Assistant"):
        st.markdown(introduction)
    column_headings.append("Mở Đầu")
    column_bodies.append(str(Introduction))

    # Write the body
    body = ""
    headings = outline_dict["body"]["headings"]
    coros = []
    for heading in headings:
        coros.append(columnist(heading, outline_dict["title"], google_search_function, get_content_function, column_function, column_summ_function, query_function))
    values = await asyncio.gather(*coros)
    count = len(values) + 2
    for i in range(2, count):
        body += "## " + roman.toRoman(i) + ". " + headings[i-2] + "\n" + values[i-2][0] +"\n"
    
    column_headings += list(headings)
    column_bodies += [value[0] for value in values]
    # Recommendation
    recommendation_function = plugin["Recommendation"]
    summContent = " ".join([value[1] for value in values])
    recommendation = await kernel.invoke(recommendation_function, sk.KernelArguments(recommendation = outline_dict["recommendations"], summContent = summContent))
    column_headings.append("Khuyến Nghị")
    column_bodies.append(str(recommendation))
    recommendation = "## " + roman.toRoman(count) + ". Khuyến Nghị \n" + str(recommendation)
    with st.chat_message("Assistant"):
        st.markdown(recommendation)

    
    #Conclusion
    conclusion_function = plugin["Conclusion"]
    summContent = " ".join([value[1] for value in values])
    conclusion = await kernel.invoke(conclusion_function, sk.KernelArguments(conclusion = outline_dict["conclusion"], summContent = summContent))
    column_headings.append("Tổng Kết")
    column_bodies.append(str(conclusion))
    conclusion = "## " +roman.toRoman(count+1) + ". Tổng Kết \n" + str(conclusion)
    with st.chat_message("Assistant"):
        st.markdown(conclusion)

    

    bio = create_docx(title, column_headings, column_bodies) #bytesio object of the docx file
    return f"""
# {title}

{introduction}

{body}

{recommendation}

{conclusion}
""", bio


st.write("""#""")
    
@st.cache_resource
def initiate_kernel():
    kernel = sk.Kernel()
    api_key, _ = sk.openai_settings_from_dot_env()
    service_id = "default"
    kernel.add_service(
        OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo-0125", api_key=api_key),
    )

    plugin = kernel.import_plugin_from_prompt_directory("./Plugins/", "ReportPlugin")
    google_plugin = kernel.import_plugin_from_object(GoogleSearchPlugin(), plugin_name = "GoogleSearchPlugin")
    return kernel, plugin, google_plugin


kernel, plugin, google_plugin = initiate_kernel()

async def main():
    
    loaded_message = False
    with st.container():
        user_input = st.chat_input("Nhập nội dung cần làm báo cáo.")
        if user_input:
            # user_proxy.initiate_chat(manager, message = user_input, silent=True)
            st.session_state["messages"].append(("User", user_input))
            for sender_name, message in st.session_state["messages"]:
                with st.chat_message(sender_name):
                    st.markdown(message)
            loaded_message = True
            report, bio = await generate_report(user_input, kernel, plugin, google_plugin)
            st.session_state["messages"].append(("Assistant", report))
            with st.chat_message("Assistant"):
                # st.markdown(report)
                if bio:
                    st.download_button(
                        label=f"{user_input}.docx",
                        data=bio.getvalue(),
                        file_name=f"{user_input}.docx",
                        mime="docx"
                    )
                        
        if "messages" not in st.session_state:
            st.session_state["messages"] = [("Manager", "Chào bạn.")]
        if not loaded_message:
            for sender_name, message in st.session_state["messages"]:
                with st.chat_message(sender_name):
                    st.markdown(message)
    #this is for outside widgets that also deletes everything

if __name__ == "__main__":
    asyncio.run(main())

