import wikipedia as wiki

def wiki_search(query, lang):

    try:
        wiki.set_lang(lang)
        page = wiki.page(query)
    except wiki.PageError:
        return f"Sorry, I couldn't find anything about <{query}>\n" \
               f"Please try it yourself: https://{lang}.wikipedia.org/wiki/{query.replace(' ', '_')}", True
    except wiki.DisambiguationError:
        return f"Sorry, your query is too vague, make it more clear and ask again!\n" \
               f"Or you can just try to find it yourself: https://{lang}.wikipedia.org/wiki/{query.replace(' ', '_')}", True
    short_sum = page.summary.split('\n')[0]
    title = f"< {page.title.upper()} >"
    link = f"For more info: {page.url}"
    return "\n\n".join((title, short_sum, link)), False


if __name__ == '__main__':
    print(wiki_search('gun', lang='en')[0])
