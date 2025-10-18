import anthropic

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="my_api_key",
)

# Replace placeholders like {{SOURCE_CODE_VERSION_1}} with real values,
# because the SDK does not support variables.
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=8192,
    temperature=0,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "You are tasked with selecting the best version of a source code file from multiple available versions. All versions are attempting to implement the same goal, but may differ in their approach, efficiency, readability, or other aspects. Your task is to analyze these versions and select the best one, or if appropriate, suggest an aggregated best result combining multiple versions.\n\nYou will be presented with different versions of the source code:\n\n<source_code_versions>\nsource_code_version_1 = \"{{SOURCE_CODE_VERSION_1}}\"\nsource_code_version_2 = \"{{SOURCE_CODE_VERSION_2}}\"\nsource_code_version_3 = \"{{SOURCE_CODE_VERSION_3}}\"\n</source_code_versions>\n\nTo evaluate and select the best version(s), follow these steps:\n\n1. Carefully read and understand the implementation goal.\n2. Review each version of the source code, paying attention to:\n   a. Correctness: Does the code accurately implement the stated goal?\n   b. Efficiency: Is the code optimized for performance and resource usage?\n   c. Readability: Is the code well-structured, properly commented, and easy to understand?\n   d. Maintainability: Is the code modular and easy to modify or extend?\n   e. Best practices: Does the code follow established coding standards and best practices for the language used?\n\n3. Compare the versions based on the above criteria. Consider the strengths and weaknesses of each approach.\n\n4. If one version clearly stands out as superior in most or all aspects, select it as the best version.\n\n5. If multiple versions have different strengths, consider whether an aggregated best result can be created by combining the best aspects of multiple versions. If so, describe how this aggregation could be done.\n\n6. Provide your analysis and selection in the following format:\n\n<thinking>\n[Provide a detailed analysis of each version, discussing their strengths and weaknesses based on the evaluation criteria.]\n[State your selection for the best version or describe the aggregated best result if applicable.]\n[Explain your reasoning for the selection, referencing specific aspects of the chosen version(s) that make it/them superior.]\n</thinking>\n\n<answer>\n[Return only the content for the final source code version file.]\n</answer>\n\nRemember to be thorough in your analysis because you have only this one chance to provide top-quality response to the user, because the user cannot message or respond you anymore."
                }
            ]
        }
    ]
)
print(message.content)
