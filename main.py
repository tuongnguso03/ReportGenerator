import asyncio, roman
import streamlit as st
from skreport import *
from Plugins.utils import create_docx

st.write("""#""")

async def main():
    loaded_message = False
    lang = st.selectbox(
        'Choose your language',
        ('English', "Vietnamese", "Tamil"))
    with st.container():
        user_input = st.chat_input("Nhập nội dung cần làm báo cáo.")
        if user_input:
            # user_proxy.initiate_chat(manager, message = user_input, silent=True)
            st.session_state["messages"].append(("User", user_input))
            for sender_name, message in st.session_state["messages"]:
                with st.chat_message(sender_name):
                    st.markdown(message)
            loaded_message = True
# Call ReportGenerator Class
            ReportGen = SKReport(user_input, lang)
# Generating Outline
            with st.spinner('Outline - Generating...'):
                await ReportGen.outlineGenerator()
            with st.chat_message("Assistant"):
                st.markdown(ReportGen.outline_dict)
                st.session_state["messages"].append(("Assistant", ReportGen.outline_dict))
            with st.spinner('Critics for Outline - Generating...'):
                critics = await ReportGen.criticGenerator(input=ReportGen.OutlineJSON, 
                                                          prompt=ReportGen.OutlineJSON_function.prompt_template.prompt_template_config.template
                                                          )
            with st.chat_message("Critics"):
                st.markdown(critics)
                st.session_state["messages"].append(("Critics", critics))
            with st.spinner('Outline - Generating...'):
                await ReportGen.outlineGenerator(critics=critics)
            with st.chat_message("Assistant"):
                st.markdown(ReportGen.outline_dict)
                st.session_state["messages"].append(("Assistant", ReportGen.outline_dict))
# Generating Intro
            with st.spinner('Introduction - Generating...'):
                await ReportGen.introGenerator()
            ReportGen.report_headings.append("Mở Đầu")
            ReportGen.report_bodies.append(str(ReportGen.introContent))
# Print out Introduction
            with st.chat_message("Assistant"):
                introduction = "## " +roman.toRoman(1) + f". Mở Đầu \n {str(ReportGen.introContent)}"
                st.markdown(introduction)
                st.session_state["messages"].append(("Assistant", introduction))
# Heading Generator
            summContent = " "
            for i, heading in enumerate(ReportGen.outline_headings):
                with st.spinner(f'Heading {i+1}/{len(ReportGen.outline_headings)} - Generating...'):
                    column, column_summ =await ReportGen.columnist(heading)
                summContent += column_summ + "\n\n"
                ReportGen.report_headings.append(heading)
                ReportGen.report_bodies.append(column)
                ## Print out content of each Heading
                with st.chat_message("Assistant"):
                    heading_print = "## " + roman.toRoman(i+2) + ". " + heading + "\n" + column +"\n"
                    st.markdown(heading_print)
                    st.session_state["messages"].append(("Assistant", heading_print))

# Conclusion Generator
            with st.spinner(f'Conclusion - Generating...'):
                await ReportGen.conclusionGenerator(summContent)
            ReportGen.report_headings.append("Kết luận")
            ReportGen.report_bodies.append(ReportGen.conclusionContent)
            with st.chat_message("Assistant"):
                conclusion_print = "## " + roman.toRoman(1 + len(ReportGen.outline_headings)) + ". " + "Kết luận" + "\n" + str(ReportGen.conclusionContent) +"\n"
                st.markdown(conclusion_print)
                st.session_state["messages"].append(("Assistant", conclusion_print))

# Recommendation Generator
            with st.spinner(f'Recommendation - Generating...'):
                await ReportGen.recommendGenerator(summContent)
            ReportGen.report_headings.append("Kiến nghị")
            ReportGen.report_bodies.append(ReportGen.recommendContent)
            with st.chat_message("Assistant"):
                recom_print = "## " + roman.toRoman(2 + len(ReportGen.outline_headings)) + ". " + "Kiến nghị" + "\n" + str(ReportGen.recommendContent) +"\n"
                st.markdown(recom_print)
                st.session_state["messages"].append(("Assistant", recom_print))

# Create Word file
            bio = create_docx(ReportGen.outline_title,
                              ReportGen.report_headings,
                              ReportGen.report_bodies,
                              )
# Download Button
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

